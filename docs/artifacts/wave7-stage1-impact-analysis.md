# Wave 7 Stage 1 — 既存テスト影響事前分析

- 作成日: 2026-06-27
- 担当: W7-B5-T44 (Sonnet L2 Spike)
- 参照: design.md §6 / requirements.md FR-W7-1 / AC-W7-1

---

## 1. 現行 regex（実コード確認）

`.claude/scripts/dashboard/parsers/tasks.py` L28:

```python
_TASK_ID_PREFIX_RE = re.compile(r"^(W\d+(?:\.\d+)?-[A-Za-z0-9]+-T\d+)")
```

`_extract_task_id()` (L109) はマッチしない場合 description 全体を ID として返す（フォールバック）。
これが「あらゆる説明文行を Task として登録する」誤抽出の根本原因。

実データ計測: 全 6 Milestone の tasks.md 走査で **チェックボックス行 378 件中、Task ID 形式 0 件**。
全行が description 全体 = Task ID として誤登録されている状態。

---

## 2. 新 regex 仕様（design.md §6 引用）

```python
TASK_ID_REGEX = r"^- \[([ x])\] (W\d+(?:\.\d+)?-[A-Z]\d+-T\d+|T\d+):"
```

FR-W7-1 / AC-W7-1 突合: Milestone 名部分を `[A-Z]\d+` に厳格化（小文字混在除外）。
`W1.5-B4-T9` は `W\d+(?:\.\d+)?` でマッチ継続（terminology.md §2 Wave 1.5 正例対応）。

---

## 3. Impacted ファイル一覧

| テストファイル | 期待値ハードコード | 件数アサーション | 破損予測 |
|:-------------|:--------------:|:------------:|:-------:|
| `test_tasks_parser.py` | ○ | ○ | 確実（3〜4 件） |
| `test_v4_view.py` | × (TaskInfo 直接構築) | × | 影響なし |
| `test_wave6_stage4_integration.py` | × (TaskInfo 直接構築) | × | 影響なし |
| `test_wave3_integration.py` | 未確認 | 未確認 | 要 L1 確認 |
| `test_wave2_integration.py` / `test_build_dashboard.py` | 未確認 | 未確認 | 要 L1 確認 |

---

## 4. 確実な破損箇所（`test_tasks_parser.py`）

| 行 | テスト名 | 破損内容 |
|:--|:--------|:--------|
| L306 | `test_parse_scans_multiple_milestones` | fixture が `W1-A1-T1:` 形式で Milestone 名 `A1`。新 regex `[A-Z]\d+` はマッチするが要実測確認。`len(tasks) == 3` が変化するリスクあり |
| L340 | `test_parse_tasks_from_both_milestones_have_correct_milestone_field` | 同上 (`W1-A1-T1:` / `W1-B1-T1:`) |
| L387 | `test_parse_mixed_milestones_includes_only_existing_tasks_md` | fixture `W1-A1-T1:` 同上 |
| L275 | `test_parse_checkbox_regex_matches_correct_pattern` | fixture が Task ID 形式を持たない行を含む。件数アサーション変化リスクあり |

---

## 5. 破損予測サマリ

- 想定破損テスト数: 概算 3〜6 件（`test_tasks_parser.py` 内 fixture 依存テスト確実 / integration 群は要確認）
- 主な破損種別: 件数ミスマッチ（`len(tasks)` アサーション）
- 実データへの影響: 現行の誤抽出 378 件が削減され、V-4 には `W7-B5-T44〜T53` 等の正規 Task ID 行のみ残る（仕様通り）

---

## 6. L1 への質問・緩和提案（L1 承認待ち）

1. **`W1-A1-T1:` 形式の扱い確認**: `[A-Z]\d+` は `A1` にマッチするが、「大文字 + 数字のみ」という制約上 `B-5` とは異なる形式。fixture の Task ID 形式を `W1-B5-T1:` 等の実プロジェクト形式に統一する緩和を T46 で適用してよいか承認依頼。

2. **integration テスト群の TasksParser 実呼び出し確認**: Bash 制限のため pytest 実行不可。L1 リレーで `pytest .claude/tests/dashboard/test_wave3_integration.py -v` 実施後に T45 着手可否を判断してほしい。
