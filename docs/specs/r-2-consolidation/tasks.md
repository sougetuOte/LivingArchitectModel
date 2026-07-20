# R-2 Milestone Tasks: 資産整理（rule 整備 / 文書精度 / 環境健全化）

## メタ情報

| 項目 | 内容 |
|:-----|:-----|
| Milestone | R-2 |
| ステータス | Draft（承認待ち） |
| 作成日 | 2026-07-20 |
| requirements | [requirements.md](./requirements.md) (Approved) |
| design | [design.md](./design.md) (Approved) |
| SPIDR 分割 | 垂直分割（Wave 内で全層貫通） |
| WBS 100% Rule | 全 FR/NFR がタスクに対応（§7 トレーサビリティ表） |
| 命名規約 | `W<n>-R2-T<m>` (Wave n / Task m) / 枝番パターン許容（例: T4a, T4b, T13b） |

---

## 1. Wave / Task 対応表（全体一覧）

**構成**: Task 22 件 + 最終検証 1 件 = 合計 23 行

| Wave | Task ID | 内容 | 担当層 | 規模 |
|:----:|:--------:|:-----|:------:|:----:|
| **W1** | W1-R2-T20 | venv 依存完全性突合 script（FR-9, FR-7） | L1/Sonnet | M |
| **W1** | W1-R2-T4a | trust-model.md カウント単位定義条項（FR-4） | Sonnet | S |
| **W1** | W1-R2-T4b | trust-model.md N 回目恒久解条項（FR-5） | Sonnet | S |
| **W1** | W1-R2-T4 | rule-002 起票（FR-6, FR-7） | Sonnet | M |
| **W1** | W1-R2-T5 | subprocess encoding 規約（FR-7） | Sonnet | M |
| **W1** | W1-R2-T6 | gabriel 契約検査 strict enum 化（FR-7） | Sonnet | M |
| **W1** | W1-R2-T7 | gabriel-metrics 環境非依存化（FR-10, FR-8） | Sonnet | S |
| **W1** | W1-R2-T8 | mode enum 拡張（FR-7） | Sonnet | S |
| **W2** | W2-R2-T9 | 文書参照 § 見出し化（FR-14, FR-8） | Sonnet | M |
| **W2** | W2-R2-T10 | ADR-0008/0004 supersede 明記（FR-14, FR-8） | Sonnet | S |
| **W2** | W2-R2-T11 | CHEATSHEET Rules 一覧現状維持確認（FR-14） | Haiku | S |
| **W2** | W2-R2-T12 | 表・節番号挿入規則明文化（FR-14, FR-8） | Sonnet | S |
| **W2** | W2-R2-T13 | 成果物ファイル命名規則（FR-14, FR-8） | Sonnet | S |
| **W2** | W2-R2-T14 | "N 件相当" 表現の説明義務（FR-14） | Sonnet | S |
| **W2** | W2-R2-T13b | 対策 B（暗黙前提明示化リスト条項）（FR-13） | Sonnet | M |
| **W3** | W3-R2-T15 | evaluation-kpi.md §7 削除（FR-11） | Sonnet | M |
| **W3** | W3-R2-T23 | deletions.md schema template 化 | Sonnet | M |
| **W3** | W3-R2-T24 | model-delegation-prompting.md scratchpad 禁止明示 | Sonnet | S |
| **W3** | W3-R2-T17 | goal-driven-l2-foreman.md plain Agent 化検討 | L1/Sonnet | M |
| **W3** | W3-R2-T25 | /code-review ultra 起動確認（調査） | Sonnet | S |
| **W3** | W3-R2-T22 | /retro skill argument default 動作（調査） | Sonnet | S |
| **W3** | W3-R2-T26 | Alembic 判断依頼 pending 記録（FR-12） | L1 | S |
| **W3** | W3-R2-終端 | 最終検証（G1）+ Milestone retro（DoD） | L1/Haiku | M |

---

## 2. W1: 基盤（rule 化候補 5 件 + trust-model 改訂 + script）

### 本 Wave で編集する PM 級ファイル一覧（K5 一括宣言）

**W1-(1) K5 一括宣言** → W1-(2) trust-model 単独承認 の 2 事象構成（design §3.2 準拠）。

#### W1-(1) K5 一括宣言（rule-002.md / subprocess-encoding-convention.md / large-scale-review/design.md）

- [ ] `.claude/rules/auto-generated/rule-002.md`（新規 / rule-001.md と同構成）
- [ ] `.claude/rules/subprocess-encoding-convention.md`（新規 / Python subprocess 編集規約）
- [ ] `docs/specs/large-scale-review/design.md`（追記 / §5.2 パターン 3 を strict enum 化向けに拡張）

#### W1-(2) trust-model.md 単独承認（FR-4, FR-5 の 2 条項）

- [ ] `.claude/rules/auto-generated/trust-model.md`（追記 / カウント単位定義 + N 回目恒久解条項）

**当 Wave 内の trust-model 改訂完了後に rule-002.md 起票コミットを実施する**（FR-6 直列依存）。

---

### W1 詳細タスク

#### **W1-R2-T20**: venv 依存完全性突合 script（FR-9 順序制約前提、FR-7 機構実装）

**概要**: `.claude/scripts/verify_import_availability.py` 新規作成。hooks/scripts/tests の全 import を走査し、`.venv` で importability 確認。

**対応仕様**:
- requirements.md FR-9（T20 は W1 先頭 / 全 rule 化 Task 先行完了）
- requirements.md FR-7（正例・誤例・grep baseline の 3 点セット）
- design.md §4.1（C1 反映の新定義：「hooks/scripts/tests 第三者 import 全数走査 vs `.venv` importability」）

**完了条件**:
- [ ] `.claude/scripts/verify_import_availability.py` 作成（NFR-2 Python 3.8 互換）
- [ ] `.claude/tests/scripts/test_verify_import_availability.py` 作成
- [ ] `bash .claude/scripts/py_invoke.sh .claude/scripts/verify_import_availability.py` 実行成功
- [ ] 正例：stdlib + インストール済 package（pytest, yaml 等）→ drift 0
- [ ] 誤例：`.venv` から意図的にパッケージ排除（monkeypatch または tmp_path で環境非依存化） → drift 検出
- [ ] grep baseline：着手時の実測 drift 件数を記録し、完了後の再計測値と比較表示

**依存**: なし（W1 先頭）

**担当想定**: L1 直作業 or Sonnet TDD

**規模**: M

---

#### **W1-R2-T4a**: trust-model.md カウント単位定義条項（FR-4）

**概要**: `.claude/rules/auto-generated/trust-model.md` に「検出イベント単位」の定義条項を新設。

**対応仕様**:
- requirements.md FR-4（検出イベント単位 = 「1 検証イベント内で検出された複数 issue は 1 カウント」）
- design.md §4.2 挿入位置 (a)（「## 閾値」節の直後に新設「## カウント単位」節）

**完了条件**:
- [ ] 「検出イベント単位」の条項が trust-model.md に存在（見出し名で特定）
- [ ] 条項に「1 検証イベント内の複数 issue = 1 カウント」の定義が明記
- [ ] rule-001 実績（4 検証イベント：2026-06-27 / 07-05 / 07-06 / 07-07）と遡及一貫
- [ ] **データソース拡張の明記（design §4.2 W-c 反映）**: 検出イベントが「tdd-patterns.log の FAIL→PASS に限らず HGA 召喚・監査 Stage・gabriel probe も含む」旨を 1 文追加

**依存**: T20 完了後に着手可

**担当想定**: Sonnet TDD

**規模**: S

**検証コマンド（FR-8 準拠）**:
```bash
grep -c "検出イベント単位" .claude/rules/auto-generated/trust-model.md
# 1 件以上ヒット確認
```

---

#### **W1-R2-T4b**: trust-model.md N 回目発火時恒久解条項（FR-5）

**概要**: trust-model.md に「N 回目発火時の恒久解検討必須化」条項を新設。

**対応仕様**:
- requirements.md FR-5（N = 3 を初期値とする。rule-001 の 3 回目発火で恒久解実施の実例）
- design.md §4.2 挿入位置 (b)（「## ルール寿命管理」節の直後に新設「## N 回目発火時の恒久解検討」節）

**完了条件**:
- [ ] 「N 回目発火時の恒久解検討」条項が trust-model.md に存在（見出し名で特定）
- [ ] N = 3 と明記
- [ ] rule-001.md の「### 拡張の根拠 (2026-07-06 / R-1 W-R1 S1 T6)」節を具体事例として参照
- [ ] 「N 回目発火時点で恒久解検討を必須化する」旨を明文化
- [ ] N の変更が PM 級である旨を記載

**依存**: T20 完了後に着手可（W1-(2) 単独承認イベント内で T4a と並行編集）

**担当想定**: Sonnet TDD

**規模**: S

**検証コマンド（FR-8 準拠）**:
```bash
grep -c "N 回目発火" .claude/rules/auto-generated/trust-model.md
# 1 件以上ヒット確認
```

---

#### **W1-R2-T4**: rule-002 起票（FR-6, FR-7 / 機構を伴う Task）

**概要**: `.claude/rules/auto-generated/rule-002.md` 新規作成。verify_reference_resolution / GitHistoryParser の parser drift 予防 rule。

**対応仕様**:
- requirements.md FR-6（T4a, T4b 承認取得後に起票 / 直列依存）
- requirements.md FR-7（正例・誤例・grep baseline の 3 点セット / 機構実体 = pytest 群）
- design.md §4.3（根拠パターン 3 検証イベント；rule-001.md の構成を踏襲）

**完了条件**:
- [ ] `.claude/rules/auto-generated/rule-002.md` 作成（rule-001.md と同構成）
- [ ] 根拠パターン表：HGA #9（2026-07-06）/ HGA #10（2026-07-07）/ W-R5 監査（2026-07-15）の 3 行（R1-059 は根拠パターン表に含めない = T6 の対象）
- [ ] ルール本文：parser 世代追随 pytest 群 (a)(b) の説明
- [ ] 正例：現行 Milestone 記法（`R-1`, `W-R1` 等）が pytest で正しく捕捉される
- [ ] 誤例：新世代架空記法（例: `S-1` / `W-S3-T7`）を旧 regex に投入 → fail 実証
- [ ] grep baseline：現行 regex が捕捉できない記法の実在件数（R1-054〜058, R1-061 対象）

**依存**: T20 完了後 + T4a, T4b 承認取得後に着手（FR-6 直列）

**担当想定**: Sonnet TDD

**規模**: M

**コミット順序（FR-6 受け入れ条件）**:
```
commit: T4a + T4b の trust-model 改訂 commit
commit: rule-002.md 起票 commit（直後の関係を記録）
```

**コミット順序検証（FR-6 検証手段）**:
```bash
git log --oneline -- .claude/rules/auto-generated/trust-model.md .claude/rules/auto-generated/rule-002.md
# trust-model 改訂 commit が rule-002 起票 commit より先行することを確認
```

---

#### **W1-R2-T5**: subprocess encoding 規約（FR-7 / 機構を伴う Task）

**概要**: `.claude/rules/subprocess-encoding-convention.md` 新規作成。LAM 内 Python subprocess 呼び出しの encoding 統一 rule。

**対応仕様**:
- requirements.md FR-7（正例・誤例・grep baseline）
- design.md §4.4（実測：r1_inventory.py は encoding 省略、r-1-git-log-usage.py は明示 → 現行混在）
- requirements.md NFR-2（Python 3.8 互換性）

**完了条件**:
- [ ] `.claude/rules/subprocess-encoding-convention.md` 作成
- [ ] 規約本文：`subprocess.run(..., text=True, encoding="utf-8", errors="replace")` を既定形
- [ ] 正例：r-1-git-log-usage.py（`encoding="utf-8", errors="replace"` 明示）
- [ ] 誤例：r1_inventory.py / git_history.py の current 実装（`encoding=` 省略） → 本 Task で修正対象
- [ ] grep baseline（design §4.4 実測値）：`grep -rn "subprocess.run(" .claude/scripts .claude/hooks .claude/tests | grep -v encoding=` の件数（着手時 / 完了後）
- [ ] 誤例による デコード失敗実証：monkeypatch で cp932 環境を模擬し UnicodeDecodeError を再現

**依存**: T20 完了後に着手可

**担当想定**: Sonnet TDD

**規模**: M

---

#### **W1-R2-T6**: gabriel 契約検査の strict enum 化（FR-7 / 機構を伴う Task）

**概要**: `verify_reference_resolution.py` に gabriel enum 検査の strictness を昇格。対象ファイルを文書系に限定し、Python ソースは pytest で別途担保。

**対応仕様**:
- requirements.md FR-7（正例・誤例・grep baseline）
- design.md §4.5（W-d, W-e 反映：検査対象を markdown ファイルに限定。python ソースは pytest enum assert で別途）
- design.md §4.5（`docs/specs/large-scale-review/design.md` §5.2 に「パターン 3（strict enum 化）」として追記）

**完了条件**:
- [ ] `verify_reference_resolution.py` に新規パターン（strict enum regex） 追加
- [ ] 検査対象：`.claude/agents/gabriel.md`, `.claude/skills/magi/SKILL.md` （文書系のみ）
- [ ] enum 3 フィールド（`verdict`, `severity`, `recommended_action`）を行頭 key-value regex で検査
- [ ] 正例：markdown ファイル内の `verdict: confirmed` 形式
- [ ] 誤例：enum フィールド名が散文中に出現するのみ（strict 化後は drift 検出）
- [ ] grep baseline（実行コマンド：`bash .claude/scripts/py_invoke.sh .claude/scripts/verify_reference_resolution.py --wave all`）の着手時 / 完了後を記録
- [ ] `docs/specs/large-scale-review/design.md` §5.2 に strict 化内容を追記確認

**依存**: T20 完了後に着手可

**担当想定**: Sonnet TDD

**規模**: M

---

#### **W1-R2-T7**: gabriel-metrics 環境非依存化（FR-10, FR-8 / 純規範文書 Task）

**概要**: `docs/artifacts/gabriel-metrics-environment-2026-07-05.md` §2 に gabriel-metrics.log のスキーマ 3 フィールド（`subject`, `anchor`, `hga_summon_ref`）を追記。

**対応仕様**:
- requirements.md FR-10（スキーマを VCS SSOT とし log 本体は gitignore 維持）
- requirements.md FR-8（検証手段 1 つ）
- design.md §4.6（既存ファイルへの追記。新規 gabriel-metrics-schema.md は作成しない）

**完了条件**:
- [ ] `docs/artifacts/gabriel-metrics-environment-2026-07-05.md` §2 の JSONL example に 3 フィールドを追加
- [ ] `mode` enum を `"aot" | "lightweight" | "widescan_verify"` に拡張
- [ ] §5「実運用開始条件」に「スキーマ全フィールド網羅の実 log entry 突合」項目を追加

**依存**: T20 完了後に着手可

**担当想定**: Sonnet TDD

**規模**: S

**検証コマンド（FR-8 準拠）**:
```bash
bash .claude/scripts/py_invoke.sh -c "
import json
fields = set()
with open('.claude/gabriel-metrics.log', encoding='utf-8') as f:
    for line in f:
        fields |= json.loads(line).keys()
print(sorted(fields))
"
```
上記出力（フィールド集合）がスキーマ文書の全フィールド名に包含されることを確認。あるいは pytest の `test_gabriel_metrics_schema.py` 等の既存テスト実行で検証可能。

---

#### **W1-R2-T8**: mode enum 拡張（FR-7 / 機構を伴う Task）

**概要**: `verify_reference_resolution.py` にパターン 4（gabriel-metrics mode enum 検査）を新設。enum 値の runtime 検証。

**対応仕様**:
- requirements.md FR-7（正例・誤例・grep baseline）
- design.md §4.7（mode enum = `{"aot", "lightweight", "widescan_verify"}`）

**完了条件**:
- [ ] `verify_reference_resolution.py` パターン 4 追加（mode enum 許可値検査）
- [ ] 正例：現行 `.claude/gabriel-metrics.log` 全 entry が enum 準拠
- [ ] 誤例：enum 外値（例: `"unknown_mode"`）を tmp_path に一時ファイル生成して drift 検出
- [ ] grep baseline（実行コマンド：`bash .claude/scripts/py_invoke.sh .claude/scripts/verify_reference_resolution.py --wave all`）の着手時点の実 log entry / 環境依存のため件数非依存設計で記録

**依存**: T20 完了後に着手可

**担当想定**: Sonnet TDD

**規模**: S

---

### W1 末ゲート（FR-15）

**各 Wave 末チェック**:
```bash
bash .claude/scripts/py_invoke.sh -m pytest
```

W1 完了時：
- [ ] G1（FR-15 準拠 / 980 PASS + 15 SKIP 以上、regression 0 維持）
- [ ] Trust-model.md 2 条項承認・merge 完了
- [ ] rule-002.md 起票・merge 完了
- [ ] T4-T8 各 Done クリア

---

## 3. W2: 文書精度（参考文書 + 暗黙前提明示化）

### 本 Wave で編集する PM 級ファイル一覧（K5 一括宣言）

- [ ] `.claude/rules/terminology.md`（追記 / §4.5 新設）
- [ ] `.claude/rules/planning-quality-guideline.md`（追記 / §1.5 新設）
- [ ] `docs/adr/0004-bash-read-commands-allow-list.md`（追記 / 関連 ADR 注記）
- [ ] `docs/adr/0008-approval-gate-redesign.md`（追記 / 関連 ADR 表）

---

### W2 詳細タスク

#### **W2-R2-T9**: 文書参照 § 見出し化（FR-14, FR-8 / 純規範文書 Task）

**概要**: LAM 内の文書参照を hardcoded 行番号（`L296` 形式）から `§` 見出し番号に置き換え。既存参照修正 + terminology.md ルール化。

**対応仕様**:
- requirements.md FR-14（文書精度 6 件の一つ）
- requirements.md FR-8（検証手段 1 つ）
- design.md §5.1（T9 対象文書リスト + grounding 訂正：`final-audit-report` / `closure-report` に 3 箇所の hardcoded 参照現存を確認）
- design.md §10「grounding 訂正」（L1 依頼文の前提誤りを訂正）

**完了条件**:
- [ ] `docs/artifacts/r-1-final-audit-report-2026-07-15.md`（L140, L182）の hardcoded `L\d+` 参照を `§` 見出し参照に修正
- [ ] `docs/artifacts/r-1-tracker-closure-report-2026-07-15.md`（L52）の hardcoded 参照を修正
- [ ] terminology.md §4.5 に「T9: 文書内相互参照は § 見出し表記を用いる」ルール追加
- [ ] grep baseline（着手時 3 箇所 → 完了後 0 箇所）

**依存**: なし

**担当想定**: Sonnet TDD

**規模**: M

**検証コマンド（FR-8 準拠）**:
```bash
grep -rE "requirements\.md.*L[0-9]+|L[0-9]+.*requirements\.md" docs/artifacts
# ヒット 0 件を確認
```

---

#### **W2-R2-T10**: ADR-0008/0004 supersede 明記（FR-14, FR-8 / 純規範文書 Task）

**概要**: ADR-0004（Bash cat/grep 無制限許可）と ADR-0008（承認ゲート再設計）の部分的関連を相互参照として明記。

**対応仕様**:
- requirements.md FR-14（文書精度 6 件の一つ）
- requirements.md FR-8（検証手段 1 つ）
- design.md §5.3（全面 supersede ではなく部分的関連 = allowlist 設計思想の変遷）

**完了条件**:
- [ ] ADR-0004 のヘッダ「関連」行に `docs/adr/0008-approval-gate-redesign.md` を追記
- [ ] ADR-0008 のメタ情報表「関連 ADR」行に ADR-0004 を追加
- [ ] 両ファイル相互参照が存在することを目視確認

**依存**: なし

**担当想定**: Sonnet TDD

**規模**: S

**検証手段（FR-8）**:
60 秒実況（受け手 = 「ADR-0004 を初めて読む後続 L1」/ 制約 = ADR-0008 の存在を知らない）：「Bash cat/grep 無制限許可の根拠を確認したい → ADR-0004 を開く → ヘッダの『関連』行に ADR-0008 参照がある → 承認ゲート再設計との関係を辿れる」経路が成立することを確認。

---

#### **W2-R2-T11**: CHEATSHEET Rules 一覧現状維持確認（FR-14 / 純規範文書 Task）

**概要**: requirements.md Non-Goals（「完全化は不要」）+ FR-14 受け入れ条件に従い、CHEATSHEET.md の Rules 一覧が「抜粋」であることの明示を現状維持確認する。ファイル自体への変更不要。

**対応仕様**:
- requirements.md §1.3 Non-Goals（T11 は「現状維持の確認」を成果として許容）
- requirements.md FR-14（完全化作業は行わない）
- design.md §5.4（軽量処理 Task）

**完了条件**:
- [ ] `grep -nE "抜粋|一覧" CHEATSHEET.md` で、Rules 一覧が「抜粋」であることの明示が現状維持されていることを確認
- [ ] 確認結果（「抜粋明示が維持されている。CHEATSHEET.md 自体への変更は不要」）を Task 完了記録に 1 行残す

**依存**: なし

**担当想定**: Haiku 事実突合

**規模**: S

---

#### **W2-R2-T12**: 表・節番号挿入規則明文化（FR-14, FR-8 / 純規範文書 Task）

**概要**: terminology.md §4.5 に「表・節番号の挿入規則」（末尾追加 / 枝番 / re-numbering の判定基準）を明文化。

**対応仕様**:
- requirements.md FR-14（文書精度 6 件の一つ）
- requirements.md FR-8（検証手段 1 つ）
- design.md §5.1（terminology.md §4.5 として § 3 小節集約。T12 は表 re-numbering 規則が主体）

**完了条件**:
- [ ] terminology.md に `## §4.5 文書参照・表記の精度規則` が新設されていることを確認
- [ ] その配下に `### T12: 表・節番号の挿入規則` 小節が存在
- [ ] 小節内容に「末尾追加 / 枝番 / re-numbering」の 3 選択肢と判定基準が明記
- [ ] 具体例（r-1-audit-tracker.md R1-059 の枝番実例）が記載

**依存**: なし（T9 との共依存なし / 独立可能）

**担当想定**: Sonnet TDD

**規模**: S

**検証コマンド（FR-8 準拠）**:
```bash
grep -n "^## §4.5 文書参照・表記の精度規則" .claude/rules/terminology.md
grep -cE "^### T(9|12|13):" .claude/rules/terminology.md
# 親見出し存在 + 3 小節の存在（3 件ヒット）確認
```

---

#### **W2-R2-T13**: 成果物ファイル命名規則（FR-14, FR-8 / 純規範文書 Task）

**概要**: terminology.md §4.5 に「成果物ファイル命名規則（起草日 vs 実行日）」を明文化。

**対応仕様**:
- requirements.md FR-14（文書精度 6 件の一つ）
- requirements.md FR-8（検証手段 1 つ）
- design.md §5.1（terminology.md §4.5 として § 3 小節集約。T13 は命名日付の選択基準が主体）

**完了条件**:
- [ ] terminology.md に `### T13: 成果物ファイル命名規則（起草日 vs 実行日）` 小節が存在
- [ ] 小節内容に「レポート・分析文書は起草日 / ログ・JSON 等は実行日」が明記
- [ ] 具体例（`retro-R1-2026-07-18.md` vs `.claude/gabriel-metrics.log` の timestamp）が記載

**依存**: なし（T9 との共依存なし / 独立可能）

**担当想定**: Sonnet TDD

**規模**: S

---

#### **W2-R2-T14**: "N 件相当" 表現の説明義務（FR-14 / 純規範文書 Task）

**概要**: requirements.md FR-14 の通り「rule 化までは不要」。本 Wave では、W1・W2・W3 内の文書編集（設計書）が「集計方法を本文中に明示する」パターンを実施することで対応（rule 化は不実施）。

**対応仕様**:
- requirements.md FR-14（T14 は rule 化不要。本 Milestone の文書内で集計方法明示パターンを模範実施）
- requirements.md FR-8（検証手段 = 「文書編集時に集計方法が明示されているか初見読者確認」）
- design.md §5.5（rule 化不要の明示）

**完了条件**:
- [ ] W1・W2・W3 内の文書編集（設計書 Task）で「N 件」表現を使用する際、括弧内に集計方法を 1 文以上明示
- [ ] 例示：「design.md §4.6 実測 4 entry（起草環境ローカル 2026-07-05 ×3, 2026-07-18 ×1）」
- [ ] Task 完了記録に「集計方法明示パターンの実施確認」を 1 行記載

**依存**: なし

**担当想定**: Sonnet TDD（各 Task の design 記述内で自然実施）

**規模**: S

---

#### **W2-R2-T13b**: 対策 B（暗黙前提明示化リスト条項）（FR-13 / 純規範文書 Task）

**概要**: `.claude/rules/planning-quality-guideline.md` に「暗黙前提明示化リスト」条項を新設。設計書起草時に、実装者が暗黙裡に補う必要のある前提をリスト化して明示することを求める。

**対応仕様**:
- requirements.md FR-13（Fable→Opus 実装ギャップ対策 / 新規追加）
- requirements.md FR-8（検証手段 = 「初見読者として 60 秒実況し違和感がないことを確認」）
- design.md §5.2（既存 §1「危険な単語リスト」の表形式に倣い、§1.5 として新設）

**完了条件**:
- [ ] planning-quality-guideline.md に `## 1.5 暗黙前提明示化リスト（設計書・仕様書向け）` が新設されている
- [ ] カテゴリ / 例 / 対処 の 3 列表に 4 行の具体例（言語標準ライブラリの癖 / 文字クラスの網羅性 / 命名体系変更時の既存 hardcode grep / 正例だけでなく誤例）が記載
- [ ] 最終行の説明文が「FR-7 と整合している旨」を記述
- [ ] design.md §5.2 の要件通り、番号付き見出し `## 1.5` を用いる（§ 記号は使わない）

**依存**: なし（W2 内で T9-T14 と並列実施可）

**担当想定**: Sonnet TDD

**規模**: M

**検証コマンド（FR-8 準拠）**:
```bash
grep -n "^## 1.5 暗黙前提明示化リスト" .claude/rules/planning-quality-guideline.md
# 節の存在を確認（§ 記号は使わない）
```

---

### W2 末ゲート（FR-15）

**各 Wave 末チェック**:
```bash
bash .claude/scripts/py_invoke.sh -m pytest
```

W2 完了時：
- [ ] G1（FR-15 準拠 / 980 PASS + 15 SKIP 以上、regression 0 維持）
- [ ] terminology.md §4.5 に T9/T12/T13 の 3 小節追加完了
- [ ] planning-quality-guideline.md §1.5 新設完了
- [ ] ADR-0004/0008 相互参照完了
- [ ] T9 hardcoded 参照修正完了（0 件確認）

---

## 4. W3: 個別消化 + 監査 + retro

### 本 Wave で編集する PM 級ファイル一覧（K5 一括宣言）

- [ ] `docs/specs/evaluation-kpi.md`（削除 / §7）
- [ ] `.claude/rules/model-delegation-prompting.md`（追記 / 新設節）

---

### W3 詳細タスク（実施順序確定 / Red 解決 #2）

#### Red 解決 #2：W3 個別消化 Task 実施順序

**判断基準（L1 確定 2026-07-20）**:
「同一 PM 級ファイルを対象とする Task は同一 Wave 内に配置済み（design §3.2 で確定済のため Wave 間分割は R-2 では発生しない）。BUILDING 中に想定外の分割が必要になった場合は FR-2 の追加宣言 + tasks.md への理由追記で扱う」

**実施順序（依存グラフ + SPIDR 分割）**:

```
T15（evaluation-kpi §7 削除）
  ↓
T23（deletions.md template 化）
  ├─ T15 の削除記録をすぐに templates として活用可能にする依存
  ↓
T24（model-delegation-prompting.md scratchpad 禁止）
  ├─ PM 級 3 ファイル（evaluation-kpi, model-delegation-prompting）の編集集約
  ↓
T17（goal-driven-l2-foreman.md plain Agent 化）
  ├─ User 判定材料提示 Task（承認待ち性のため中盤）
  ↓
T25（/code-review ultra 確認）
  ├─ contingency リスク（settings.json 追加宣言可能性あり）のため T17 後
  ↓
T22（/retro skill argument）
  ├─ 調査のみで設定変更なし / 低優先度のため末尾
  ↓
T26（Alembic pending 記録）
  ├─ 完了条件なし / 記録のみ
  ↓
最終検証（G1 + Milestone retro / G2〜G5 は段階導入途上のため DoD 非依存）
```

**根拠 1 行ずつ**:
- **T15 → T23**: 削除 Task の直後に deletions template を確定することで、同型の削除 tracking を structure化できる（Postel's Law）
- **T23 → T24**: PM 級ファイル編集の集約。evaluation-kpi 削除直後に model-delegation-prompting 追記で「文書削除・追記の一連作業」として完結させる
- **T24 → T17**: 設定以外の変更完了後に、user 判定が必要な foreman.md 検討に遷移（順序に固い理由なし / pure contingency 優先度の都合）
- **T17 → T25**: T17 が user 判定を要するため、T25 の contingency（settings 追加宣言）に先行させる（settings は確定後に回す設計）
- **T25 → T22**: T25 で settings 変更が発生しない場合のみ T22 に遷移。settings 変更発生時は FR-2 追加宣言に遷移（但し R-2 内では未発生想定）
- **T22 → T26**: 調査-only Task を低優先度末尾に配置。応答待ち記録（T26）は全 Task 完了後に統合

---

#### **W3-R2-T15**: evaluation-kpi.md §7 削除（FR-11 / 純規範文書 Task）

**概要**: `evaluation-kpi.md` の §7「KPI ダッシュボード」を完全削除。grep 実測で仕様参照 0 件を確認。

**対応仕様**:
- requirements.md FR-11（§7 完全削除 / §2-6 無変更）
- requirements.md FR-8（検証手段 1 つ）
- design.md §6.1（C2 反映の grep 判定手順 / 仕様参照 0 件を削除条件）

**完了条件**:
- [ ] 検索コマンド実行：`grep -rnE "evaluation-kpi.*§7|KPI ダッシュボード" .`（リポジトリルート）
- [ ] ヒットを 2 分類：仕様参照（docs/specs/ 配下・ただし `docs/specs/r-2-consolidation/` は除外 / docs/internal/ / .claude/ / CLAUDE.md / CHEATSHEET.md）vs 時点記録（docs/artifacts/ / 本 tasks.md 自身を含む = 削除条件に効かない）
- [ ] 仕様参照が **0 件** であることを確認（r-2-consolidation/ 配下は時点記録として除外）
- [ ] `evaluation-kpi.md` から §7（見出し「## 7. KPI ダッシュボード」から次の `---` 区切り線の直前まで）を削除
- [ ] `git diff docs/specs/evaluation-kpi.md` で §2-6（12-140 行目相当）が無変更であることを確認

**依存**: なし

**担当想定**: Sonnet TDD

**規模**: M

**Contingency（FR-11 記載通り）**:
仕様参照が発見された場合は削除を保留し、PM 級判定に差し戻す。

---

#### **W3-R2-T23**: deletions.md schema template 化（専用 FR なし / FR-8 準用）

**概要**: `docs/artifacts/r-1-deletions.md` の既存列構造（6 列 + commit 列）を独立 field として template 化。LAM 側 SSOT として `docs/artifacts/` 配下に新設。また T15 で削除する evaluation-kpi.md §7 の記録を deletions.md に反映する際の活用方法を示す。

**対応仕様**:
- requirements.md §6 素材トレーサビリティ（T23）
- requirements.md FR-8（検証手段 1 つ）
- design.md §6.2（T23：deletions.md 6 列 + commit 列 / 使用例 1 件以上記載）

**完了条件**:
- [ ] `docs/artifacts/r-1-deletions.md` の既存列名を確認（grep で列構造を取得）
- [ ] template 形式（YAML frontmatter または markdown 表の固定列化）を決定
- [ ] 新規 template ファイル（`docs/artifacts/deletions-template.md` 相当）を作成
- [ ] 列名を正確に転記 + 使用例を 1 件以上記載

**検証手段（FR-8）**: `grep -nE "commit" docs/artifacts/deletions-template.md` で commit 列の存在を確認 + 初見読者として 60 秒実況し使用例だけで記入方法が分かることを確認

**依存**: T15 完了後に着手可（推奨順序 / ハード依存ではない。T15 の削除事例が新しいうちに template を書けるため）

**担当想定**: Sonnet TDD

**規模**: M

---

#### **W3-R2-T24**: model-delegation-prompting.md scratchpad 禁止明示（専用 FR なし / FR-8 準用）

**概要**: `.claude/rules/model-delegation-prompting.md` に「scratchpad 書込禁止」を明示する新設節を追加。§2「Sonnet 5 委譲プロンプト必須 7 項」直後に配置。

**対応仕様**:
- requirements.md FR-14（個別 Task）
- requirements.md FR-8（検証手段 1 つ）
- design.md §6.2（T24）

**完了条件**:
- [ ] model-delegation-prompting.md に「task boundaries」或いは新規「## Subagent Boundary Protection」節を追加
- [ ] 節内容に「scratchpad ファイル（`C:\Users\...\AppData\Local\Temp\claude\...`）への書込禁止」を明記
- [ ] 本 Task の委譲プロンプト（当 tasks.md の task boundaries セクション）の「scratchpad 書込禁止」文言を叩き台として使用

**依存**: なし（T15 と並列可 / ただし T24 は順序上 T15 の直後が自然）

**担当想定**: Sonnet TDD

**規模**: S

**検証手段（FR-8）**:
```bash
grep -n "scratchpad" .claude/rules/model-delegation-prompting.md
# 1 件以上ヒット確認
```

---

#### **W3-R2-T17**: goal-driven-l2-foreman.md plain Agent 化検討（専用 FR なし / FR-8 準用）

**概要**: `.claude/agents/goal-driven-l2-foreman.md` の Agent 権限（現行 = 限定 `Agent(goal-driven-l3-executor)`）を plain `Agent` に拡張すべきか否かを、user 判定材料として整理。設計判断は行わず、選択肢と影響（nested spawn 可否）のみ提示。

**対応仕様**:
- requirements.md FR-14（個別 Task）
- requirements.md FR-8（検証手段 1 つ）
- design.md §6.2（T17 / 調査 Task）

**完了条件**:
- [ ] `.claude/agents/goal-driven-l2-foreman.md` 冒頭の frontmatter で current `tools` 宣言を確認（L7 info 反映：`Read, Glob, Grep, Agent(goal-driven-l3-executor)`）
- [ ] 冒頭に「検討議題」セクションを追加：
  - 現行設定（限定 Agent）の implications
  - plain Agent 化の implications（nested spawn 無制限化）
  - 各選択肢の メリット・デメリット（1-2 文）
- [ ] User に判定を仰ぐ旨を明記

**依存**: なし

**担当想定**: L1 直作業 or Sonnet TDD

**規模**: M

**検証手段（FR-8）**:
60 秒実況（受け手 = 「このエージェントを使う後続 L1」/ 制約 = 前提知識ゼロ）：「ツール権限を plain Agent に変更すべきか判定したい → 当ファイルを開く → 『検討議題』セクションで選択肢と影響が明記されている → どの判定をすべきか理解できる」経路が成立することを確認。

---

#### **W3-R2-T25**: /code-review ultra 起動確認（調査）（専用 FR なし / FR-8 準用）

**概要**: Claude Code の built-in `/code-review ultra` 起動が `.claude/settings.json` `permissions.allow` で阻害されていないか確認。調査のみで rule 化は行わない。contingency = 結果が settings.json 変更に帰着した場合は追加宣言が必要。

**対応仕様**:
- requirements.md FR-14（個別 Task）
- requirements.md FR-8（検証手段 1 つ）
- design.md §6.2（T25 / 調査 Task）

**完了条件**:
- [ ] `.claude/settings.json` の `permissions.allow` に `/code-review ultra` 起動を阻害する項目がないか確認（grep で `/code-review` 検索）
- [ ] 調査結果（「allow 制約が存在しない / または存在して阻害している」）を Task 完了記録に記載
- [ ] 阻害が存在する場合のみ：変更内容 1 行 + FR-2 追加宣言が必要である旨を後続記録に明記

**依存**: なし

**担当想定**: Sonnet TDD

**規模**: S

**Contingency**:
調査結果が settings.json 変更に帰着した場合、同ファイルは §3.2 表に含まれない PM 級ファイルのため、FR-2 の追加宣言（当初宣言に含まれない新規 PM 級ファイル）が R-2 内で必要になる。その場合は SESSION_STATE.md に記録し、ユーザー承認を求める。

---

#### **W3-R2-T22**: /retro skill argument default 動作（調査）（専用 FR なし / FR-8 準用）

**概要**: `/retro` skill の argument default 動作を Claude Code 公式ドキュメント（context7 `/websites/code_claude`）で確認。設定変更は行わず、調査のみ。低優先度。

**対応仕様**:
- requirements.md FR-14（個別 Task）
- requirements.md FR-8（検証手段 1 つ）
- design.md §6.2（T22 / 調査 Task）

**完了条件**:
- [ ] context7 または公式 Claude Code docs で `/retro` skill の argument 構成を確認
- [ ] 調査結果（「default 動作 = 〇〇である / または不明」）を Task 完了記録に記載

**依存**: なし

**担当想定**: Sonnet TDD

**規模**: S

---

#### **W3-R2-T26**: Alembic 判断依頼 pending 記録（FR-12 / 純規範文書 Task）

**概要**: Alembic 側への判断依頼内容を pending 記録として `docs/artifacts/r-2-t26-pending.md` に保存。応答待ちであり、R-2 の DoD が本項目の解決に非依存であることを明記。

**対応仕様**:
- requirements.md FR-12（T26 は外部応答に依存 / DoD 非依存）
- design.md §6.3（T26 pending 記録設計）

**完了条件**:
- [ ] `docs/artifacts/r-2-t26-pending.md` 作成
- [ ] Alembic 側への判断依頼内容の要約（1-3 段落）
- [ ] 応答待ちである旨
- [ ] 「R-2 の DoD が本項目の解決に非依存である」の明記

**依存**: なし

**担当想定**: L1 直作業

**規模**: S

---

### W3 末ゲート（FR-15 + Milestone DoD）

#### **最終検証**:

```bash
bash .claude/scripts/py_invoke.sh -m pytest
```

- [ ] G1（FR-15 準拠 / 980 PASS + 15 SKIP 以上、regression 0 維持）
  - **注記**: G2〜G5 は R-1 期同様に段階導入途上のため、R-2 では G1 のみを明示的なゲート条件とする。R-2 Milestone COMPLETE 判定は G1 維持を必須とし、G2〜G5 は DoD 非依存
- [ ] R-2 変更 rule/script の相互参照リンク切れなし
- [ ] T15 evaluation-kpi §7 削除完了 + diff 確認
- [ ] T23-T25 各 Task 完了
- [ ] T26 pending 記録完成

#### **Milestone retro**:

- [ ] `docs/artifacts/retro-R2-<date>.md` 起草
- [ ] DoD-4（承認イベント実績 = 宣言イベント単位 + ダイアログ実数）を記録
- [ ] NFR-3（目標 4±1 回）と実績の差分を分析
- [ ] すべての Red（§7）が解決済みであることを確認

---

## 5. Wave 末ゲート手順（全 Wave 共通 / FR-15 準拠）

**各 Wave 末（W1末、W2末、W3末）で必ず実施**:

```bash
bash .claude/scripts/py_invoke.sh -m pytest
```

**確認事項**:
- pytest 実行成功（exit code 0）
- PASS 件数が 980 以上（＋ SKIP 15 相当）
- regression なし（既存 PASS テストの FAIL 化なし）

**実行結果**（PASS/SKIP 件数）を各 Wave 末の Task 完了記録に残す。

---

## 6. トレーサビリティ検証（WBS 100% Rule）

### 全 FR/NFR → Task 対応表

| FR/NFR | タイプ | 対応 Task | Wave | 完了条件 |
|:-------|:-----:|:----------|:---:|:---------|
| FR-1 | 構造 | W1/W2/W3 分離 | All | 3 Wave のみで構成 |
| FR-2 | プロセス | K5 一括宣言 / 信託 | All | 各 Wave 冒頭に宣言セクション存在 |
| FR-3 | 判定基準 | tasks.md Red 解決 #1 | §4 | 「同一 PM 級 Task は同一 Wave 内」を明文化 |
| FR-4 | 実装 | W1-R2-T4a | W1 | trust-model.md 検出イベント単位定義 |
| FR-5 | 実装 | W1-R2-T4b | W1 | trust-model.md N 回目恒久解条項 |
| FR-6 | 実装 | W1-R2-T4 | W1 | rule-002.md 起票（T4a, T4b 後） |
| FR-7 | 実装 | W1-R2-T4, T5, T6, T8, T20 | W1 | 正例・誤例・baseline 3 点セット |
| FR-8 | 実装 | W1-R2-T7, W2-R2-T9, T10, T12, T13, T14, W3-R2-T17, T22, T23, T24, T25 | All | 検証手段 1 つ |
| FR-9 | 実装 | W1-R2-T20 | W1 | T20 が W1 先頭 / 全 rule Task 先行 |
| FR-10 | 実装 | W1-R2-T7 | W1 | gabriel-metrics schema 文書化 |
| FR-11 | 実装 | W3-R2-T15 | W3 | evaluation-kpi §7 削除 |
| FR-12 | 実装 | W3-R2-T26 | W3 | pending 記録作成 / DoD 非依存明記 |
| FR-13 | 実装 | W2-R2-T13b | W2 | planning-quality-guideline 対策 B |
| FR-14 | 実装 | W2-R2-T9, T10, T11, T12, T13, T14 | W2 | 文書精度 6 件（T11 は現状維持確認を成果として許容 / 対策 B は FR-13 行参照） |
| FR-15 | 実装 | Wave 末ゲート | All | 各 Wave 末で 980+ PASS 維持 |
| NFR-1 | 原則 | 全 Task | All | Zero-Regression Policy 実行 |
| NFR-2 | 原則 | T20, T5 他 Python | W1 | Python 3.8 互換 / `from __future__ import annotations` |
| NFR-3 | 管理 | Milestone retro | W3 | 承認イベント実績 4±1 回記録 |

**検証結果**: 全 15 FR + 3 NFR = 18 項目が Task に対応。孤児タスクなし。

---

## 7. 未解決質問（Red / PLANNING 内解決済み）

### Red 解決 #1：FR-3 Wave 間分割判断基準

**解決内容**:
「同一 PM 級ファイルを対象とする Task は同一 Wave 内に配置済み（design §3.2 で確定済のため Wave 間分割は R-2 では発生しない）。BUILDING 中に想定外の分割が必要になった場合は FR-2 の追加宣言 + tasks.md への理由追記で扱う」

**根拠**: design.md §3.2 の PM 級ファイル一覧（全 10 ファイル）を Wave 別に整理した結果、同一ファイルの複数 Wave での編集が発生しない設計になっていることを確認。

---

### Red 解決 #2：W3 個別消化 Task 実施順序

**解決内容**: 本 §4 の「W3 詳細タスク（実施順序確定 / Red 解決 #2）」で確定（優先度都合による便宜的決定）。

実施順序: **T15 → T23 → T24 → T17 → T25 → T22 → T26 pending + 最終検証**

根拠 1 行ずつ（上記参照）。

---

## 参照

- `docs/specs/r-2-consolidation/requirements.md` (Approved / 本 tasks 入力)
- `docs/specs/r-2-consolidation/design.md` (Approved / Task 詳細設計)
- `.claude/rules/auto-generated/trust-model.md`（FR-4, FR-5 改訂対象）
- `.claude/rules/auto-generated/rule-001.md`（rule-002 の兄弟）
- `.claude/rules/terminology.md` / `planning-quality-guideline.md` / `model-delegation-prompting.md`（編集対象）
- `docs/adr/0004-bash-read-commands-allow-list.md` / `docs/adr/0008-approval-gate-redesign.md`（supersede 明記対象）
- `docs/artifacts/r-1-final-audit-report-2026-07-15.md` / `docs/artifacts/r-1-tracker-closure-report-2026-07-15.md`（T9 修正対象）
- `docs/specs/evaluation-kpi.md`（T15 削除対象）
- `.claude/agents/goal-driven-l2-foreman.md`（T17 検討対象）
- `docs/specs/large-scale-review/design.md`（T6, T8 참고対상）

---

## 変更履歴

| 日付 | 変更者 | 内容 |
|:-----|:-------|:-----|
| 2026-07-20 | L1 (Direct Executor) | 初版起草（requirements.md + design.md 正本化 / Red 2 件解決明文化 / 全 Task 詳細 + 依存グラフ） |
