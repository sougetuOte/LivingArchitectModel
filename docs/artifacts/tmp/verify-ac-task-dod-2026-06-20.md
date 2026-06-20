# AC ↔ Task DoD トレース検証（2026-06-20）

## 検証結果サマリ

| 項目 | 結果 |
|------|------|
| 全 AC 件数 | 11 |
| AC ↔ Task マッピング | 11/11 割当済み（100%） |
| 検証手段あり | 11/11 （100%） |
| テスト可能性 high/medium | 11/11 （100%） |
| **総合判定** | **PASS** |

---

## AC ↔ Task DoD 詳細トレース

| AC ID | AC 本文（要約） | 担当 Task | 対応 FR | DoD 検証手段 | テスト可能性 | 状態 |
|-------|---------------|----------|--------|-----------|------------|------|
| AC-1 | NFR-6/7/8 行削除 | T1, T2, T3 | FR-1.1, 1.2, 1.3 | grep + テキスト照合 | high | OK |
| AC-2 | §6.3 注釈差し替え | T3 | FR-1.3 | grep `grep "NFR-6\|NFR-7\|NFR-8"` | high | OK |
| AC-3 | NFR-14a 「v5 Phase 1」更新 | T5 | FR-1.5 | テキスト照合 | high | OK |
| AC-4 | NFR-17 「手動スナップショット」差し替え | T4 | FR-1.4 | テキスト照合 | high | OK |
| AC-5 | `evaluation-kpi.md` 「Wave 2 完了前」削除 | T4 | FR-1.4 | grep コマンド | high | OK |
| AC-6 | `distill()` C-1〜C-4 空スキップ実装 | T6 | FR-2.1, 2.2 | pytest テストケース | high | OK |
| AC-7 | 3 件テスト追加 + 既存 21 件 PASS | T7 | FR-2.3 | pytest 全テスト実行 | high | OK |
| AC-8 | commit c674ec8 存在確認 | T9 | （実施済み確認） | git log コマンド | high | OK |
| AC-9 | SKILL.md Step 4 警告ラベル追記 | T10 | FR-4.1 | grep + テキスト照合 | high | OK |
| AC-10 | `magi-skill.md` 警告ラベル同期 | T12 | FR-4.3 | diff コマンド | high | OK |
| AC-11 | `future-candidates.md` gabriel 統合記録 | T13 | FR-4.4 | ファイル存在 + テキスト照合 | high | OK |

---

## 検証手段の具体性確認

### AC-1: NFR-6/7/8 行削除確認

**担当タスク**: W7-B4-T1, T2, T3

**DoD 検証手段**:
- `grep -rn "NFR-6" docs/` で参照先を確認（実行可能）
- `grep "NFR-6\|NFR-7\|NFR-8" docs/specs/v4.0.0-immune-system-requirements.md` で削除確認（実行可能）
- テキスト照合で HTML コメント挿入確認（観測可能）

**テスト可能性**: `high` — grep コマンドで機械的に検証可能

---

### AC-2: §6.3 注釈差し替え確認

**担当タスク**: W7-B4-T3

**DoD 検証手段**:
- `grep "ループ実行時間の計測は NFR-15/16" docs/specs/v4.0.0-immune-system-requirements.md`（実行可能）
- 差し替え前後のテキスト照合（観測可能）

**テスト可能性**: `high` — grep で確認可能

---

### AC-3: NFR-14a 「v5 Phase 1」更新確認

**担当タスク**: W7-B4-T5

**DoD 検証手段**:
- `grep "v5 Phase 1 で計測スクリプト" docs/specs/v4.0.0-immune-system-requirements.md`（実行可能）
- テキスト照合で完全文字列一致を確認（観測可能）

**テスト可能性**: `high` — grep で確認可能

---

### AC-4: NFR-17 「手動スナップショット」差し替え確認

**担当タスク**: W7-B4-T4

**DoD 検証手段**:
- `grep "/quick-save 実行時に K1〜K5" docs/specs/v4.0.0-immune-system-requirements.md`（実行可能）
- テキスト照合（観測可能）

**テスト可能性**: `high` — grep で確認可能

---

### AC-5: `evaluation-kpi.md` 「Wave 2 完了前」削除確認

**担当タスク**: W7-B4-T4

**DoD 検証手段**:
- `grep "Wave 2 完了前" docs/specs/evaluation-kpi.md` の出力が空（実行可能）
- 設計書 §1.5 「変更後」テキストが反映されたか確認（観測可能）

**テスト可能性**: `high` — grep で空出力を確認可能

---

### AC-6: `distill()` 空スキップ実装確認

**担当タスク**: W7-B4-T6

**DoD 検証手段**:
- `_is_grader_log_empty()` 関数の実装確認（코드 읽기）
- C-1〜C-4 AND 条件の実装確認（코드 읽기）
- `distill()` 내 삽입 위치 확인（코드 읽기）
- `logging.getLogger(__name__).info()` 출력 확인（코드 읽기）

**テスト可能性**: `high` — pytest テストケースで검증가능

**対応 pytest テスト**（T7 に記載）:
- `test_empty_grader_log_skips_entry`
- `test_partial_fields_not_skipped`
- `test_skip_log_output`

---

### AC-7: テスト追加 + PASS 確認

**担当タスク**: W7-B4-T7

**DoD 検証手段**:
- `pytest .claude/scripts/tests/test_distill_lessons.py -v` で新規 3 件 PASS（実行可能）
- `pytest .claude/scripts/tests/` で既存 21 件 + 新規 3 件 = 24 件全 PASS（実行可能）
- `caplog` で `distill-lessons: skipped (empty grader log)` ログ捕捉（테스트 内で 검증）

**テスト可能性**: `high` — pytest で実行・検証可能

---

### AC-8: commit c674ec8 存在確認

**担当タスク**: W7-B4-T9

**DoD 検証手段**:
- `git log --oneline | grep c674ec8`（実行可能）
- `grep -c "現状 no-op" .claude/skills/full-review/SKILL.md` の出力が `4` である（実行可能）
- git diff で Stage 1/3 の行が削除されていないことを確認（実行可能）

**テスト可能性**: `high` — git/grep コマンドで機械的に検証可能

---

### AC-9: SKILL.md Step 4 警告ラベル追記確認

**担当タスク**: W7-B4-T10

**DoD 検証手段**:
- `grep "WARNING: temporary preserve" .claude/skills/magi/SKILL.md` で 1 件ヒット（実行可能）
- テキスト照合で警告ラベル文言が requirements.md FR-4.1 と一字一句一致（観測可能）
- git diff で Step 4 以外が変更されていないことを확인（실행 가능）

**テスト可能性**: `high` — grep + diff で確認可能

---

### AC-10: `magi-skill.md` 警告ラベル同期確認

**担当タスク**: W7-B4-T12

**DoD 検証手段**:
- `diff <(grep -A 7 "WARNING:" .claude/skills/magi/SKILL.md) <(grep -A 7 "WARNING:" .claude/skills/lam-orchestrate/references/magi-skill.md)` で diff が空（実行可能）
- 두 파일의 경고 레이블 문언이 정확히 동일한지 확인（관찰 가능）

**テスト可能性**: `high` — diff コマンドで자동 검증 가능

---

### AC-11: `future-candidates.md` gabriel 統合記録確認

**担当タスク**: W7-B4-T13

**DoD 検証手段**:
- `grep -A 20 "FC-1\|gabriel" docs/specs/v5-fat-reduction/future-candidates.md` でエントリ존재확인（실행 可能）
- テキスト照合で以下 4 項目が記載されているか확인（관찰 可能）:
  - 対象: MAGI Reflection の gabriel adversarial probe への統合
  - 設計根拠: ADR-0005 Reflection 追補
  - 統合方針
  - 実施条件: v5 ② gabriel エージェント設計・ADR 新設との同時実施

**テスト可能性**: `high` — grep + テキスト照合で確認可能

---

## 문제점の有無

### 検証手段なし AC
なし（全 11 件で DoD に検証手段が明記）

### テスト可能性 low の AC
なし（全 11 件で実行可能コマンドまたは観测可能な状態が定義）

### AC-Task マッピング欠落（Orphan）
なし（全 11 AC が Task に割当）

### Task-AC マッピング欠落（Ghost Task）
以下のタスクが直接 AC に対応していないが、FR 対応またはゲート機能のため問題なし:

| Task | 対応 | 理由 |
|------|-----|-----|
| W7-B4-T8 | FR-2.4（実装前ゲート） | 설계 정합성 확인 |
| W7-B4-T11 | FR-4.2（rules/ 변경） | MAGI SKILL.md 변경 후 추가 |
| W7-B4-T14 | FR-4.5（사후 검증） | AoT 분해 温存 확인（事後검증） |

---

## 結論

**総合評価: PASS**

- ✅ 全 11 AC が Task に割当済み
- ✅ 全 Task の DoD に「実行可能なコマンド or 観測可能な状態」を記載
- ✅ テスト可能性が high/medium のみ
- ✅ grep/pytest/git/diff/テキスト照合 いずれかの「検証手段」が明記
- ✅ WBS 100% Rule 充足（Gap 0 件、Orphan 0 件、Ghost Task 0 件）

**AC ↔ Task DoD トレース： 完全整合**

