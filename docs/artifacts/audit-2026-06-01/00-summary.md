# whole-project 品質監査 Pass 1 — 統合サマリー

日付: 2026-06-01 / フェーズ: AUDITING / 対象: コード面 S1〜S4（`.claude/hooks/` 5,585 LOC）
手段: 6 並列 read-only 監査（Sonnet 発見）→ Opus 精査・統合
判定基準: [code-quality-guideline.md](../../../.claude/rules/code-quality-guideline.md)（Critical/Warning/Info）

## 集計

| サブシステム | レポート | Critical | Warning | Info | 評価 |
|---|---|---|---|---|---|
| S1 コア hooks | [S1](S1-core-hooks.md) | 3 | 5 | 3 | Yellow |
| S2a analyzers 基盤 | [S2a](S2a-analyzers-infra.md) | 1 | 5 | 3 | Yellow |
| S2b card_generator | [S2b](S2b-card-generator.md) | 1 | 7 | 4 | Yellow |
| S2c 言語アナライザ | [S2c](S2c-analyzers-lang.md) | 2 | 5 | 4 | Yellow |
| S3 autonomous | [S3](S3-autonomous.md) | 2 | 4 | 3 | Yellow |
| S4 テスト | [S4](S4-tests.md) | 0 | 7 | 3 | Yellow |
| **計** | | **9** | **33** | **20** | **Yellow** |

> 注: 下記「Opus 精査」で Critical の一部は重大度を再評価。実 blocking 数は精査後の値を正とする。

## Opus 精査・訂正

### 訂正1: S1 Critical #1 / 横断懸念は過大評価（層1 実装済みを反映せず）
- S1 エージェントは `pre-tool-use.py` 88-92行の**陳腐化コメント**（「層1 は T1-5 後に別途固定」）を読み「二重防御が実質層2のみ」と推論。だが**層1 `settings.autonomous.json` は実装済み（commit `5af4a63`）**。
- `_read_current_phase` の例外時 `""` 返却で層2 FR-9 が沈黙する件は実在するが、**層1（決定的・current-phase.md 非依存）が書込を阻止**するため設計どおり（二重防御の意義）。→ **Critical → Warning** に降格。層2 堅牢化（例外時に安全側へ倒す）は妥当だが破滅的でない。
- 真の派生指摘: **`pre-tool-use.py` 88-92行コメントの陳腐化**（doc-drift・SE 修正）。

### 高信頼 Critical（S1×S3 独立収束・実コード確認済み）
`lam-stop-hook.py` `_handle_autonomous`（266行〜）:
1. **fail-open**: `autonomous-state.json` 読取失敗で `_stop()`（停止/完了許可）。`_run_g1_checker`「障害=FAIL(2)」のフェイルセーフ方針と逆。FR-4.1b 観点で `_block()` 方向が妥当。
2. **再帰ガード未適用**: `stop_hook_active` を見て早期 exit しない（design D1/D3 未実装）。block cap=8 と相互作用し `max_iterations=20` の意図が活きない懸念。
→ 偽陽性の可能性低。**SC-1/SC-7 実走行前に修正すべき**。

## 修正トリアージ（CP-B の順序案）

### 即修正候補（PG/SE・blocking 性が高い順）
- `lam-stop-hook.py` autonomous fail-open + 再帰ガード（SE・上記 Critical 2件）
- `analyzers/` の Silent Failure 群（SE）: `run_pipeline.py:162` 行数固定 / `gitleaks_scanner.py:213` 例外メッセージ漏洩 / `rust_analyzer.py:145` JSONDecodeError 無音 / `javascript_analyzer.py:77` ESLint returncode=2 無音 / `orchestrator` 系 RecursionError 握り潰し
- `pre-tool-use.py` 88-92行 陳腐化コメント修正（SE doc-drift）
- `state_manager`/`card_generator` の save_ 無保護（SE）

### PM 判断（自動修正しない）
- `settings.autonomous.json` の `docs/specs/**` deny 要否（FR-3.4 解釈）
- root `tests/` ↔ `.claude/hooks/tests/` の重複/diverge 解消方針
- `card_generator.py` 1,305行の責務分割（大規模 = 別途 /building）

### テスト追加（SE・S4）
- `scale_detector` 全関数 / autonomous 障害 path / FR-9 deny / PostToolUseFailure 分岐 / 壊れ state.json graceful stop

## 横断テーマ
- **Silent Failure が最頻**: 解析失敗を log のみで空結果返却 →「問題なし」誤認。LAM の Error Swallowing 禁止（Critical 基準）に直結。
- **save/load の信頼性非対称**: load は try 保護、save は無防備。
- **テスト穴**: 新規ロジック・error path の網羅不足。

## スコープ外（Pass 2 / 別タスク）
- 統治・ドキュメント整合（S5 ルール矛盾 / S6 spec↔code ドリフト / S7 skills 整合）は Pass 2。

## 適用ログ（CP-B）

### B2: analyzers Silent Failure に観測性追加（2026-06-01・SE）
- `gitleaks_scanner.py:213` 例外メッセージを固定文言化（path/env 露出回避・詳細は既存ログ）
- `rust_analyzer.py` cargo audit JSONDecodeError 時に `logger.warning` 追加（無音 `[]` 解消）
- `javascript_analyzer.py` ESLint rc∉{0,1} 時に `logger.warning` 追加（無音 `[]` 解消）
- テスト: main 119 passed / root 20 passed（回帰なし）

### Opus 精査の追加訂正（適用時に判明）
- **card_generator `detect_circular_dependencies`/`build_topo_order`/`analyze_impact`**: RecursionError は**既に `logger.warning` 済み**（894行等）。S2b の「log だけで握り潰し・呼出元が知る手段なし」は過大評価＝**観測性は既存**。残課題は「`[]` 戻り値が"循環なし"と区別不能」という戻り値契約のみ（リファクタ＝PM/別途 /building・B2 対象外）。

### 未適用（保留）
- B1（autonomous fail-open）/ B3（doc-drift + save_ 保護）/ B4（テスト追加）: 未着手
- run_pipeline.py:162 line_count: 意味論要確認
- PM 保留3件（docs/specs deny / 2スイート統合 / card_generator 分割）

> 進捗: read-only 発見（Pass 1）完了 → B2 適用済み。残 B は順次。
