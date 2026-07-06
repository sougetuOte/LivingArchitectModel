# R-1 W-R2 観測値記録 (認知複雑度・重複コード)

**記録日**: 2026-07-07 (W-R2 S4-T3 / NFR-1 補足)
**目的**: W-R2 (module 1/2/4 消化 Wave) で実測された複雑度・重複・規模の観測値を記録する。閾値判定 (Green State) には使用しない参考データ (NFR-1 補足の位置づけ)。

## 1. 規模観測 (実測 / wc -l・git 実測)

| 対象 | before (W-R2 開始時) | after (W-R2 完了時) | 差分 | 契機 |
|:-----|--------------------:|-------------------:|-----:|:-----|
| `.claude/scripts/dashboard/builder.py` | 936 行 (git HEAD 実測 / tracker 起票時 921 は旧時点) | **539 行** | **-397** | R1-003 第一歩 (CSS/JS 切出し) |
| `.claude/scripts/dashboard/static_assets.py` | - (新規) | 441 行 | +441 | 同上 (移動 / byte-identical 検証済) |
| dashboard テスト群 (R1-031 対象 7 ファイル) | - | 正味 -71 行 | -71 | R1-031 fixture 共通化 |
| テストスイート | 537 PASS + 14 SKIP (W-R2 開始時) | **579 PASS + 14 SKIP** | +42 | R1-001/006/053/002 のテスト追加 + R1-007/008 の新規テスト |

## 2. 重複コード観測

- **R1-031 (解消済)**: MilestoneInfo/WaveInfo/TaskInfo の手動構築が 10 ファイルに散在。実測では**型名言及 87 / 実構築呼び出し 52** (計測基準の乖離を tracker resolution に記録)。conftest.py factory fixture 3 種に集約し 49 箇所移行 (モデル仕様直接検証 3 箇所は意図的残置)
- **計測手法の教訓**: `grep -c` の型名カウントは「言及」と「構築」を区別しない。今後の重複計測は呼び出し形 (`Name(`) ベースを正とする

## 3. 認知複雑度・SRP 観測

- **DashboardBuilder (R1-003)**: 921→936 行に肥大していた God Class 傾向は第一歩 (静的合成 422 行相当の切出し) で 539 行に縮小。**残る V1-V4 ビュー分割は W-R5 retro 議題** (個々のメソッド責務は明確 / 即時分割は Zero-Regression 上リスク過大の判断を維持)
- **gd_state.py (727 行 / R1-I06)**: 最大ファイルだが 21 独立小関数で SRP 維持 / 分割不要と裁定済 (行数単独では複雑度指標にならない実例)
- **verify_reference_resolution.py**: R1-053/R1-056 系の regex 層 hole が「1 ファイル内の同型 bug class 連鎖」として 3 度 (R1-006→053→056) 検出された。複雑度ではなく **regex 仕様の暗黙 scope が発生源** — W-R3 以降の R1-056 消化時に scope 明文化 (R1-057 推奨対応) とセットで処理すべき

## 4. プロセス観測 (参考)

- 2 段階検出パターン (L2 実装 → HGA adversarial verify) は W-R2 で 2 回機能 (HGA #9 → R1-053-055 / HGA #10 → R1-056-059)。**L2 が構造的に検出できない残存攻撃面を毎回 1+ 件検出**しており、監査インフラ系修正への適用は費用対効果あり
- Sonnet 5 委譲指針 (model-delegation-prompting.md / 2026-07-07 制定) 適用後の L2 委譲 4 回で境界逸脱 0 / 早期終了 0 / 自己申告による有益な訂正 2 件 (87→52 計測乖離 / 921→936 行数乖離)

## 参照

- `docs/artifacts/r-1-audit-tracker.md` (R1-002/003/031/053 resolution)
- `docs/specs/large-scale-review/tasks.md` §W-R2 S4
- `.claude/rules/model-delegation-prompting.md`
