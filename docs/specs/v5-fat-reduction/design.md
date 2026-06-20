# 設計書: v5 fat 削減リファクタ

- バージョン: 0.1.0
- 作成日: 2026-06-20
- ステータス: Draft（PM 承認待ち）
- 根拠文書: `docs/specs/v5-fat-reduction/requirements.md`（FR-1.1〜FR-4.5）
- 参照文書: `docs/artifacts/v5-fat-audit-2026-06-19.md`（B-4 監査レポート）

---

## 0. Problem Statement（設計視点）

要件定義書（§1）が定義した 4 種類の fat を「実装可能な変更単位」に分解する。

| fat 種別 | 設計上の問題 | 設計解 |
|---------|------------|-------|
| ゾンビ NFR（NFR-6/7/8/17） | 仕様書に行が残り、参照者が「有効な要件」として誤認する | 行削除 + HTML コメント + 注釈差し替え |
| 計測実態乖離（NFR-14a） | 「完了」マークがあるが計測ゼロ。将来タスクの根拠が不明 | NFR テキスト更新 + future-candidates 起票 |
| 空振り書き込み（distill_lessons.py） | grader ログが空でも lessons.md に書き込む。低品質エントリが蓄積する | 書き込み前スキップ条件の挿入 |
| no-op Step 無表示（SKILL.md） | 前提条件未充足の Step が稼働するように見える | マーカー追記（実施済み: c674ec8） |
| 形骸化手続き（MAGI Reflection） | 形式実行で効果ゼロが実機計測で裏付けられた | 警告ラベル付き温存（v5 ② gabriel 統合まで） |

---

## 1. Non-Goals（非スコープ）

要件書 §2 Non-Goals をそのまま継承し、設計でも以下は対象外とする:

- gabriel エージェントの設計・実装（v5 ② 別マイルストーン）
- MAGI Reflection の物理削除またはコメントアウト
- `/full-review` Stage 1/3 の物理撤去
- NFR-17 の「自動集計スクリプト実装」（プラン B は不採用）
- distill-lessons セマンティック重複チェック（プラン C）
- `/retro` Step 4 への lessons.md 確認手順追加（プラン B・v5 PLANNING 時に統合）
- goal-driven-orchestration 仕様書における NFR-6/7/8（これらは v4.0.0-immune-system とは別番号体系で、フォールバック機構・既存競合・grader 検収を指す。削除対象外）

---

## 2. Alternatives Considered

### §1 NFR cleanup の却下案

**案 X: 削除せずに "参考値マーク" を付与して温存する**

NFR-6/7/8 の行を削除せず、「拘束度」列を「努力目標（実装なし・参考値）」に更新し、注釈で「計測基盤整備後に見直す」と明記する案。

- メリット: 行が残ることで「将来計測したい意図」が明示される。参照先のリンク切れが発生しない
- 却下理由:
  1. NFR-6/7 は仕様書本文が既に「努力目標」と宣言しており、「参考値マーク付与」は現状維持と同義。fat が解消されない
  2. 計測実装が存在しない要件を仕様書の一行として残すことは「将来実装されるかもしれない要件」という誤解を生む
  3. audit §1.2 が結論付けた「削除コスト最小・リスク最小」の評価と矛盾する
  4. v5 で NFR-15/16 の可観測性基盤が整備された後に計測を実施する方針は、削除後の注釈（「ループ実行時間の計測は NFR-15/16 整備後に実施する」）でも十分に表現できる

### §2 distill-lessons の却下案

**案 B: スキップせず空エントリを追記し、後段の `/retro` Step 4 で除去する**

grader ログが空であってもエントリを追記し、「状態: 未検証・情報なし」とラベル付けして、`/retro` Step 4 の人間精査で不要エントリを削除する案。

- メリット: 実行の痕跡がすべて lessons.md に残り、追跡性が向上する
- 却下理由:
  1. `/retro` が実行されない場合、空エントリが無制限に蓄積し続ける（audit §2.3 で月 20 タスク × 6 ヶ月 = 120 エントリ蓄積予測）
  2. 「追記する情報が物理的に存在しない」ケースと「情報はあるが未検証」を同じエントリ形式で扱うと、精査者が情報ゼロのエントリに時間を費やす
  3. `/retro` の精査コストが上がると精査頻度が下がり、結果として品質劣化が加速する
  4. プラン A（grader ログ空スキップ）は SE 級（内部ロジック変更・公開 API 不変）で即時実施可能

### §3 SKILL.md no-op マーカー（実施済み確認）

却下案は発生しない（commit c674ec8 で既に実施済み。本章は記録目的のみ）。

### §4 MAGI Reflection 警告ラベルの却下案

**案 A: Reflection を完全廃止（Step 4 を SKILL.md から削除する）**

- メリット: 形骸化ステップが即時除去される。アンカーファイルから定型文「致命的な見落とし: なし → 結論確定」が消える
- 却下理由:
  1. adversarial 検証ゼロになる。ADR-0005 Reflection 追補が示した「独立文脈での検証が 3 catch を発見」パターンの足場が失われる
  2. v5 ② gabriel adversarial probe へ統合する際に、Reflection の構造・位置情報が設計地ならしとして機能する。先に削除すると設計コストが増加する
  3. audit §4.4 プラン A は「廃止による直接コスト削減効果は限定的」と評価しており、即時廃止のメリットが小さい

---

## 3. Success Criteria

| 観測可能な条件 | 計測方法 | 対応 AC |
|--------------|---------|--------|
| `v4.0.0-immune-system-requirements.md` §6.3 の NFR-6/7/8 行が存在しない | `grep "NFR-6\|NFR-7\|NFR-8" docs/specs/v4.0.0-immune-system-requirements.md` の出力に §6.3 テーブル行がない | AC-1 |
| §6.3 の注釈が差し替え後の文に一致する | 当該行のテキスト照合 | AC-2 |
| §6.4 の NFR-14a テキストが「v5 Phase 1 で計測スクリプトを実装」を含む | テキスト照合 | AC-3 |
| §6.5 の NFR-17 テキストが「手動スナップショット」を含む | テキスト照合 | AC-4 |
| `evaluation-kpi.md` §6.2 の「Wave 2 完了前」条件分岐が存在しない | テキスト照合 | AC-5 |
| `distill()` に C-1〜C-4 全条件の空スキップが実装されている | `pytest .claude/hooks/tests/test_distill_lessons.py` FAIL=0 | AC-6 |
| 既存テスト 21 件 + 新規 3 件が全 PASS | `pytest .claude/hooks/tests/` で FAIL=0 | AC-7 |
| commit c674ec8 が master ブランチに存在し、4 Step のマーカーが確認できる | `git log --oneline | grep c674ec8` | AC-8 |
| MAGI SKILL.md Step 4 冒頭に警告ラベルが存在する | テキスト照合 | AC-9 |
| `magi-skill.md` 参照コピーの警告ラベルが SKILL.md と文言一致する | `diff` コマンドまたはテキスト照合 | AC-10 |
| `future-candidates.md` に gabriel 統合設計記録が存在する | ファイル存在確認 + テキスト照合 | AC-11 |

---

## §1 設計: NFR cleanup の diff

### 1.1 diff 対象ファイルと対象セクション

対象ファイル: `docs/specs/v4.0.0-immune-system-requirements.md`
現状確認: L531〜L574 の §6.1〜6.5 テーブル群

> **注意**: `docs/specs/goal-driven-orchestration/` 配下の NFR-6/NFR-7/NFR-8 は別番号体系（フォールバック機構・既存競合排除・grader 検収を指す）。削除対象ではない。削除前に grep で参照箇所を特定し、v4.0.0 仕様書の参照のみを対象とすること。

### 1.2 §6.3 パフォーマンス: FR-1.1〜1.3 の diff

**変更前（L547〜L554、現状）:**

```
### 6.3 パフォーマンス

| ID | 要件 | 目標値 | 拘束度 |
|----|------|--------|--------|
| NFR-6 | PG 権限フックの応答時間 | 数秒程度（command 型） | 努力目標 |
| NFR-7 | SE 権限フックの応答時間 | 体感で待てる範囲（prompt 型） | 努力目標 |
| NFR-8 | 1ループサイクルの実行時間 | プロジェクト規模に依存。計測・可視化を優先 | 参考値 |
| NFR-9 | コンテキスト残量の最低保証 | 20%（これ以下で強制停止） | **必須** |

> NFR-6〜8 は厳密な制約ではなく、運用の中で適正値を見極める。計測基盤（NFR-15〜17の可観測性）を先に整え、実績データに基づいて閾値を設定する方針。NFR-9（コンテキスト残量）のみがハード制約。
```

**変更後（FR-1.1/1.2/1.3 適用後）:**

```
### 6.3 パフォーマンス

| ID | 要件 | 目標値 | 拘束度 |
|----|------|--------|--------|
| NFR-9 | コンテキスト残量の最低保証 | 20%（これ以下で強制停止） | **必須** |

> ループ実行時間の計測は NFR-15/16 の可観測性基盤が整備された後に実施する。
```

**NFR-V1 対応（HTML コメント）:**

NFR-6/7/8 を参照するファイルに以下の HTML コメントを挿入する。grep 結果より、v4.0.0-immune-system-requirements.md 以外では `docs/design/hooks-python-migration-design.md:289` が NFR-6 参照箇所として特定されている（audit §1.2 記述）。

コメント形式:
```
<!-- NFR-6 は v5 fat 削減で削除済み (2026-06-20)。`docs/specs/v5-fat-reduction/requirements.md` 参照 -->
```

**参照箇所一覧（実装前に再 grep で確認すること）:**

現時点で grep 確認された参照先:
- `docs/specs/v4.0.0-immune-system-requirements.md:549,550,551` — 削除対象行本体（HTML コメント挿入位置は削除後の直後の行）
- `docs/design/hooks-python-migration-design.md:289` — NFR-6 への計測タスク言及（HTML コメント挿入対象）
- `docs/artifacts/v5-fat-audit-2026-06-19.md` — 監査記録（参照元として削除免除）

参照先のうち、audit 記録・specs/v5-fat-reduction 配下は「削除済みを記録する文書」であるため HTML コメント不要。

### 1.3 §6.4 セキュリティ: FR-1.5 の diff（NFR-14a 更新）

**変更前（L564、現状）:**

```
| NFR-14a | フック分類の誤判定率を Wave 1 完了後に計測し、ベースラインを確立する |
```

**変更後（FR-1.5 適用後）:**

```
| NFR-14a | フック分類の誤判定率を v5 Phase 1 で計測スクリプトを実装し、ベースラインを確立する（現状: 実計測ゼロ・計測スクリプト未実装。Wave 1 完了チェック済みだが内容未達） |
```

### 1.4 §6.5 可観測性: FR-1.4 の diff（NFR-17 差し替え）

**変更前（L572、現状）:**

```
| NFR-17 | 運用KPI の定期集計（`/daily` コマンドとの連携） |
```

**変更後（FR-1.4 適用後）:**

```
| NFR-17 | 運用 KPI の手動スナップショット（`/quick-save` 実行時に K1〜K5 の値を人間が記録する。自動集計スクリプトの実装はオプション） |
```

### 1.5 evaluation-kpi.md §6.2 の差し替え（FR-1.4 連動）

対象ファイル: `docs/specs/evaluation-kpi.md`

**変更前（L136〜L144、現状）:**

```
### 6.2 ベースライン未確立時の出力

Wave 2 完了前は以下を表示:

```
### KPI サマリー
ベースライン未確立（Wave 2 完了後に計測開始）
現在の計測データ蓄積状況: [ログファイル数]件
```
```

**変更後（FR-1.4 適用後）:**

```
### 6.2 任意集計時の出力

K1〜K5 の定義を維持するが集計は任意（オプション）。
`/quick-save` 実行時に人間が手動でスナップショットを記録する。
自動集計スクリプトを実行する場合は §6.1 のテンプレートを使用する。
```

### 1.6 既存仕様間の参照リンク影響評価

NFR-6/7/8/17/14a を参照する他文書の grep 調査結果:

| 参照 ID | 参照元ファイル | 行番号（概算） | 対処方針 |
|--------|------------|-------------|--------|
| NFR-6 | `docs/specs/v4.0.0-immune-system-requirements.md` | L549 | 削除対象行本体 |
| NFR-7 | `docs/specs/v4.0.0-immune-system-requirements.md` | L550 | 削除対象行本体 |
| NFR-8 | `docs/specs/v4.0.0-immune-system-requirements.md` | L551 | 削除対象行本体 |
| NFR-6 | `docs/design/hooks-python-migration-design.md` | 289 | HTML コメント挿入 |
| NFR-17 | `docs/specs/v4.0.0-immune-system-requirements.md` | L572 | テキスト差し替え |
| NFR-14a | `docs/specs/v4.0.0-immune-system-requirements.md` | L564 | テキスト更新 |
| NFR-14a | `docs/tasks/v4.0.0-immune-system-tasks.md` | L425 | 完了チェック注釈追加（「内容未達」を補記） |
| NFR-6〜8 | `docs/artifacts/v5-fat-audit-2026-06-19.md` | 各所 | 削除免除（監査記録） |
| NFR-6〜8 | `docs/specs/v5-fat-reduction/requirements.md` | 各所 | 削除免除（本仕様書の根拠記述） |

> 実装前に `grep -rn "NFR-6\|NFR-7\|NFR-8\|NFR-17\|NFR-14a" docs/` で再確認し、上記以外の参照先が追加されていないことを検証すること。

---

## §2 設計: distill-lessons grader ログ空スキップのフロー

### 2.1 現状フロー（distill_lessons.py）

`distill()` 関数（L217〜L247）の現状処理順序:

```
distill(task_id, grader_log_paths, ...) 呼び出し
  ↓
L238: target_path = lessons_path or _default_lessons_path()
L239: grader_logs = _load_grader_logs(grader_log_paths)
       ← ファイル不在・JSON エラーのファイルはスキップ。結果は空リストの可能性あり
  ↓
L241-244: 重複チェック（既存実装）
  if target_path.exists():
      if task_id in target_path.read_text(...):
          return   ← task_id 重複時スキップ
  ↓
L246: entry = build_lesson_entry(task_id, grader_logs, verified)
  ← grader_logs が空でもエントリを生成する（ループ回数 0・修正内容不明・定型文）
  ↓
L247: _append_to_lessons(target_path, entry)
  ← lessons.md に追記される
```

問題箇所: L239 で `grader_logs = []` になった場合（ファイル不在・JSON 不正・ログ空）でも L246 が `build_lesson_entry` を呼び、`ループ回数: 0`・`修正内容: 修正内容不明`・`一般則: 定型文` の低品質エントリが生成される。

### 2.2 追加するスキップ条件分岐の挿入位置

FR-2.2 MUST 要件「grader ログ空スキップは L241 の task_id 重複チェックより先に評価する」に準拠し、L239 と L241 の間に挿入する。

**変更後のフロー:**

```
L239: grader_logs = _load_grader_logs(grader_log_paths)
  ↓
[新規挿入: グレーダーログ空スキップ判定] ← FR-2.1 で追加
  if _is_grader_log_empty(grader_logs):
      logger.info("distill-lessons: skipped (empty grader log)")
      return
  ↓
L241-244: 重複チェック（既存実装・変更なし）
  ↓
L246-247: エントリ構築・追記（既存実装・変更なし）
```

挿入行番号（目安: 現行 L240 の直後）。実装時は `_load_grader_logs()` 呼び出し直後、`if target_path.exists():` ブロックの直前に配置する。

### 2.3 C-1〜C-4 の判定関数シグネチャ案

FR-2.1 で定義された 4 条件を単一ヘルパー関数にまとめる。

```python
def _is_grader_log_empty(grader_logs: list[dict]) -> bool:
    """grader ログが全条件を満たす「情報ゼロ」状態かどうかを返す（FR-2.1 C-1〜C-4）。

    全条件が True の場合のみ True を返す（AND 条件）。
    1 条件でも False になればスキップしない（MUST NOT）。

    C-1: ループ回数（grader_logs の長さ） == 0
    C-2: 全 grader_log の fail 原因フィールドが空文字列/null/未設定
    C-3: 全 grader_log の修正内容フィールドが空文字列/null/未設定
    C-4: 全 grader_log の一般則フィールドが空文字列/null/定型文/またはそれらの組み合わせ

    注意:
    - C-1 が True（len==0）の場合、C-2〜C-4 は grader_log が存在しないため自動的に True
    - 定型文（C-4）の判定は build_lesson_entry() が生成する固定文字列と照合する
    """
```

C-4 の「定型文」は `build_lesson_entry()` L175 が生成する以下の文字列を参照する:
```
「（自動抽出・要人間確認）ループ完了時の修正パターンを参照のこと」
```

この文字列と完全一致、または空文字列・null の場合を「定型文のみ」と判定する。

C-2/C-3 の「fail 原因フィールド」「修正内容フィールド」は grader log の JSON スキーマを参照する。grader log の実際のスキーマキーは `_extract_fail_reasons()` (L90-105) と `_extract_fix_summary()` (L108-129) の実装を確認の上、対象フィールドを特定すること。

### 2.4 ログ出力フォーマット

FR-2.1 指定のログ出力文字列: `distill-lessons: skipped (empty grader log)`

**出力先の選定**: `logging` 標準ログ機構（`logging.getLogger(__name__).info(...)` レベル）を使用する。`print()` / `sys.stderr.write()` は使用しない。

選定理由:
1. 既存 `main()` 関数が `print(f"[distill-lessons] 蒸留完了: ...")` を標準出力に書いているため、スキップ通知も同一レイヤーに揃えたい
2. ただし「蒸留完了」は CLI 呼び出し時の最終確認メッセージであり、スキップは内部ロジック判定のため severity を分ける
3. `logging.INFO` で出力することで CLI 利用時（`--log-level` フラグ等）のフィルタリングに対応できる
4. 既存テスト `test_distill_lessons.py` が `capsys`（stdout/stderr 捕捉）を使用している可能性があるため、標準ストリームへの直接書き込みは避けてテスト安定性を維持する

> 実装前に `test_distill_lessons.py` の既存テストが logging モックを使っているか `capsys` を使っているかを確認し、テスト側の整合性を確保すること。

### 2.5 既存テスト 21 件への影響評価

`distill()` 関数に新規スキップ条件を追加した場合の既存テストへの影響:

| テストケース種別 | 影響可能性 | 理由 |
|---------------|---------|------|
| grader_logs が非空（pass/fail エントリあり）のテスト | 影響なし | C-1 が False となり、スキップ条件に該当しない |
| task_id 重複テスト（`test_duplicate_task_id_not_appended_twice`） | 影響なし | 重複チェックの前にスキップが先行するが、このテストは grader_logs を非空にしている前提 |
| `_load_grader_logs` の単体テスト | 影響なし | `distill()` に依存しない |
| `build_lesson_entry` の単体テスト | 影響なし | `distill()` に依存しない |
| `distill()` に空の grader_log_paths を渡すテスト | 要確認 | 現状 pass していた場合、新規スキップ条件により動作が変わる可能性がある |

> 実装前に `pytest .claude/hooks/tests/test_distill_lessons.py -v` を実行し、21 件の現状 PASS を確認した上でスキップ条件を追加すること。

### 2.6 FR-2.3: 追加する新規テスト関数の設計

```python
def test_empty_grader_log_skips_entry(tmp_path):
    """grader ログが空リストのとき distill() がエントリを追記しないことを確認する。
    
    C-1 が True（grader_log_paths に存在するファイルがなく _load_grader_logs が [] を返す）
    の場合に、lessons.md が作成されないことを検証する。
    """

def test_partial_fields_not_skipped(tmp_path):
    """C-1 が False（ループ回数 1 件以上）の場合はスキップしないことを確認する。

    grader_logs に pass/fail エントリが 1 件以上あれば、
    C-2〜C-4 が True でもスキップしないことを検証する（AND 条件）。
    """

def test_skip_log_output(tmp_path, caplog):
    """スキップ時に 'distill-lessons: skipped (empty grader log)' が logging.INFO で出力されることを確認する。
    
    `caplog` フィクスチャで logging.INFO レベルのメッセージを捕捉する。
    """
```

---

## §3 設計: SKILL.md no-op マーカー（実施済み確認の記録）

### 3.1 commit c674ec8 の diff 構造

commit c674ec8（`docs(skills): full-review SKILL.md に no-op マーカー追記（B-4 ③ 方針 X）`）により、以下 4 箇所にマーカーが追記された。

各マーカーの形式:

```
> **⚠️ 現状 no-op（[前提条件]のため）— 2026-06-19 監査確認**: [理由の詳述]。[充足条件] が実装された時点で有効化される。（B-4 §3 方針 X 採用）
```

### 3.2 4 Step のマーカー位置記録

| Step | ファイル内位置（grep 確認済み） | no-op の理由 | 有効化条件 |
|------|---------------------------|------------|----------|
| Stage 1 Step 3（依存グラフ構築） | L231〜 `### Step 3: 依存グラフ構築（FR-7a）` の直後 | `import-map.json` が未生成のため `import_map` が常に `{}` に縮退 | `ast-map.json` / `import-map.json` 生成実装後 |
| Stage 2 Step 1-2（チャンク分割） | Stage 2 Step 1/2 の各冒頭（tree-sitter 要求箇所） | `tree-sitter` 未インストール。従来モードに常にフォールバック | `tree-sitter` インストール + Plan B 有効化 |
| Stage 3 Step 1（Layer 2 モジュール統合） | L517〜 `**入力**:` 行の直後 | `ast_map = {}` 縮退・`detect_module_boundaries([])` が空リスト処理 | Plan C（100K 行超）有効化 + `ast-map.json` 生成実装後 |
| Stage 3 Step 3（Layer 3 機械的チェック） | L586〜 `### Step 3: Layer 3 — システムレビュー（機械的チェック）` の直後 | `import_map = {}` 縮退・`detect_circular_dependencies({})` が常に空リスト | Plan C + `import-map.json` 生成実装後 |

マーカーの存在は `grep "現状 no-op" .claude/skills/full-review/SKILL.md` で 4 件ヒットすることで確認済み。

### 3.3 受け入れ条件（AC-8）の確認手順

1. `git log --oneline | grep c674ec8` — commit の存在確認
2. `grep -c "現状 no-op" .claude/skills/full-review/SKILL.md` — 出力が `4` であること
3. `grep -n "Stage 1/3" .claude/skills/full-review/SKILL.md` — 物理削除されていないことを確認（行が存在すること）

---

## §4 設計: MAGI Reflection 警告ラベルの文言

### 4.1 警告ラベル最終確定版（FR-4.1）

requirements.md FR-4.1 に記載された文言をそのまま採用する。以下が確定版:

```markdown
> **[WARNING: temporary preserve / v5② gabriel 統合予定]**
> Reflection（Step 4）は形式実行の状態にある。
> B-4 監査（2026-06-19）の実機計測では、9 件の適用事例中 7 件が記録済みで、
> 初回変更率 0%（全件「致命的な見落とし: なし → 結論確定」）であった。
> 根本原因は Step 3 (CASPAR) 直後の同一文脈再処理による入力同一問題。
> 物理削除は行わない。v5 ② で gabriel adversarial probe として機能強化予定。
```

### 4.2 挿入位置の特定

**SKILL.md（`.claude/skills/magi/SKILL.md`）:**

現状 L79 が `### Step 4: Reflection（振り返り）` 行。警告ラベルはこの行の直後（L80 の直前）に挿入する。

挿入後の構造:

```
L79: ### Step 4: Reflection（振り返り）
L80: [空行]
L81: > **[WARNING: temporary preserve / v5② gabriel 統合予定]**
L82: > Reflection（Step 4）は形式実行の状態にある。
...（警告ラベル 7 行）
[空行]
L90: 全員で結論を検証する。**1 回限り**。
```

**lam-orchestrate 参照コピー（`.claude/skills/lam-orchestrate/references/magi-skill.md`）:**

現状 L78 が `### Step 4: Reflection（振り返り）` 行（SKILL.md と同一構造を確認済み）。同一位置（L78 直後）に同一文言を挿入する。

### 4.3 decision-making.md の挿入位置

`.claude/rules/decision-making.md` で Reflection 関連の行（grep 確認済み）:

```
L18: 4. **Reflection（新規追加）**: 全員で結論を検証（1回限り）。致命的な見落としがあれば修正
L39: AoT Decomposition → MAGI Debate (各Atom) → Reflection → AoT Synthesis
L56: ### Reflection
L57: 致命的な見落とし: なし → 結論確定
```

挿入対象: L18 の行末、または L18 の直後の行に以下を追加する:

```
   > [WARNING] B-4 監査（2026-06-19）実機計測: 初回変更率 0% / v5 ② gabriel 統合予定
```

> FR-4.2 に従い、`rules/` 配下の変更は **PM 級**（承認ゲート）。BUILDING フェーズ着手前に人間の承認を得ること。

### 4.4 SKILL.md と参照コピーの同期方針（FR-4.3）

BUILDING 実装後に以下のコマンドで文言一致を検証する:

```bash
# 警告ラベル部分を抽出して diff
grep -A 7 "WARNING: temporary preserve" .claude/skills/magi/SKILL.md > /tmp/magi-warning.txt
grep -A 7 "WARNING: temporary preserve" .claude/skills/lam-orchestrate/references/magi-skill.md > /tmp/ref-warning.txt
diff /tmp/magi-warning.txt /tmp/ref-warning.txt
# 出力が空（差分なし）であること
```

### 4.5 AoT 分解の温存範囲（FR-4.5）

警告ラベル挿入は Step 4（Reflection）のみを対象とする。以下は変更不可:

| 要素 | 場所 | 変更可否 |
|------|------|--------|
| Step 0: AoT Decomposition | SKILL.md L38〜L54 | 変更不可（FR-4.5 MUST NOT） |
| Step 1: Divergence | SKILL.md L56〜L61 | 変更不可 |
| Step 2: Debate | SKILL.md L63〜L65 | 変更不可 |
| Step 3: Convergence | SKILL.md L67〜L77 | 変更不可 |
| Step 5: AoT Synthesis | SKILL.md L94〜L105 | 変更不可 |
| Step 4 の本文（警告ラベル以外） | SKILL.md L80〜L93 | 変更不可（警告ラベルを先頭に追加するのみ） |

根拠: AoT 分解は W5-T2 で 6 件の隠れリスクを顕在化した実績を持つ独立機構（audit §4.6 PM 決定「AoT 分解は温存」）。

---

## 5. ADR 候補

以下の決定事項は将来の ADR として記録を推奨する（本設計書が暫定的に意思決定の根拠を記録する）:

1. **NFR-6/7/8 削除 vs 注釈化**
   - 選択肢: 削除 / 参考値マーク付与（案 X）
   - 選択: 削除（行レベル）
   - 理由: 仕様書が既に「努力目標」と宣言しており、温存の追加価値がない

2. **MAGI Reflection の処遇**
   - 選択肢: 完全廃止（案 A）/ 警告ラベル付き温存（採用）/ 真の再評価化（案 C）
   - 選択: 警告ラベル付き温存
   - 理由: v5 ② gabriel adversarial probe への設計地ならしを保持するため。ADR-0005 §Reflection 追補が示す独立文脈検証パターンを失わない

---

## 6. 非機能要件（実装上の制約）

| ID | 要件 | 設計での対応 |
|----|------|-----------|
| NFR-V1 | §1 の変更箇所に HTML コメントを残す | §1.2 で挿入位置と文言を確定 |
| NFR-V2 | §2 の変更後、既存テスト 21 件が PASS を維持する | §2.5 で影響評価済み。挿入位置が L241 前のため既存処理は変更なし |
| NFR-V3 | §4 の警告ラベルは SKILL.md と参照コピーで文言一致 | §4.4 で diff コマンドによる検証手順を定義 |
