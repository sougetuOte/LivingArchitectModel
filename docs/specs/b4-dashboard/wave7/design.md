# b4-dashboard Wave 7 — design.md

- バージョン: 0.2.3
- 作成日: 2026-06-27
- 更新日: 2026-06-27（v0.2.3 = v0.2.2 + spec-critic 4 回目レビュー反映 / Critical 3 + Warning 4 + Info 3 対処）
- ステータス: **Approved**（v0.2.3 PM 補追承認 2026-06-27 / spec-critic 4 回目盲点解消）
- 根拠文書: `docs/specs/b4-dashboard/wave7/requirements.md` v0.2.1
- 参照文書:
  - `docs/specs/b4-dashboard/design.md` v0.3.0 §5「Assignee タグ規約」（commit `4448d4c`）
  - `docs/specs/b4-dashboard/wave6/design.md` v0.3.0（直近 Wave / 改修パターン参照元）
  - `docs/artifacts/2026-06-27-magi-wave7-planning.md`（MAGI 合議 = 本設計の決定根拠）
- 設計方針: MAGI Atom A4 で **「元 design.md §5 を SSOT とし wave7/design.md は追加事項のみ」** 確定

---

## §1 Problem Statement

Wave 7 requirements.md §1 で示された 3 件の data 仕様問題（TasksParser 誤抽出 / Assignee 列無価値化 / 複数 Milestone 比較不能）を解消する。
設計観点で追加する問題は以下:

| 問題 | 設計上の影響 |
|:-----|:-----------|
| TasksParser の現行 regex がチェックボックス行全般を Task として取り扱う | 厳格化 regex 導入時に既存の正常 Task が漏れない保証が必要（後方互換 NFR-W7-4） |
| Assignee タグの抽出ロジックを既存 description パースに追加 | description 末尾切り出しと既存 description 表示の整合（V-4 表示で `@<assignee>` 文字列が二重に出ないこと） |
| V-2 の現状実装が「単一 Milestone エントリ前提」 | 複数 Milestone 一覧化時のソート順 / 表示構造 / CSS 予算管理 |
| Wave 6 達成値（Lighthouse 97 / CSS 9,922 bytes）の退行リスク | 追加 CSS は残 318 bytes 内 / V-2 構造変更で aria-* 維持 |

---

## §2 Non-Goals（設計スコープ外）

- 元 design.md §5 の **再記述・移転**（MAGI Atom A4 で確定 / SSOT を一本化）
- builder.py の全面リファクタリング（必要最小限の変更）
- V-3 Wave 一覧ビューの構造変更（Wave 7 では V-2 のみ拡張）
- 横並び表示 / フィルタトグル / タブ切替（requirements §3 Non-Goals 継承）
- TasksParser の正規表現エンジンの差し替え（標準 `re` モジュール継続）

---

## §3 Alternatives Considered

### A3-1: TasksParser Task ID regex（FR-W7-1 対応）

3 つの方式を MAGI で評価:

| Alternative | 内容 | 採否 | 理由 |
|:-----------|:-----|:----|:-----|
| (a) 厳格 regex（**採用**） | `^(W\d+-[A-Z]\d+-T\d+|T\d+):` 形式のみ抽出 | ✅ | requirements §4 FR-W7-1 と整合 / 既存 Task 全件保持確認可能 |
| (b) ホワイトリスト | tasks.md の冒頭に「有効 Task ID 一覧」セクションを設け、それ以外は無視 | ❌ | 運用負荷大 / 既存 tasks.md 全件改修必要 |
| (c) 文脈解析 | description の文章解析で「Task らしさ」を判定 | ❌ | 過剰実装 / regex で十分 |

→ **(a) 採用**。

### A3-2: Assignee タグ抽出位置（FR-W7-2 対応）

| Alternative | 内容 | 採否 |
|:-----------|:-----|:----|
| (a) 行末固定（**採用 / 元 §5 既存**） | `\s+@([A-Za-z0-9_-]+)\s*$` で行末から切り出し | ✅ |
| (b) 行頭 | description 先頭の `@<assignee>` を抽出 | ❌（運用習慣として後置の方が読みやすい） |
| (c) 専用カラム | tasks.md にカラム追加 | ❌（後方互換破壊） |

→ **(a) 採用**（元 design.md §5 の規約に従う / 本書での再決定なし）。

### A3-3: 複数 Milestone 一覧化の表示方式（FR-W7-4 対応）

MAGI Atom A3 で 4 option を評価し **option 4（全 Milestone 一覧化）** 採用。

| Option | 内容 | 採否 |
|:-------|:-----|:----|
| (1) 横並び表示 | 複数 Milestone を横カラム並列 | ❌（responsive 負荷大 / Lighthouse 退行リスク） |
| (2) フィルタトグル | チェックボックスで選択可 | ❌（Wave 7 では実装しない / 後方互換で将来追加可） |
| (3) タブ切替 | Milestone ごとにタブ | ❌（比較体験弱 / chip 意図に反する） |
| (4) 全 Milestone 一覧化（**採用**） | 全 Milestone を縦に列挙 | ✅（CSS のみで実現 / responsive 負担小 / 現状 2 件で十分） |

→ **(4) 採用 + フィルタは将来追加可能な設計**（HTML 構造を Milestone 単位のセクションに分割）。

### A3-4: V-2 の表示順序（FR-W7-4 対応）

| Alternative | 内容 | 採否 |
|:-----------|:-----|:----|
| (a) Milestone 名昇順（**採用**） | 例: B-4 → B-5 | ✅（決定論的・テスト容易） |
| (b) 最新更新順 | SESSION_STATE.md 内の出現順 | ❌（決定論的でない / SESSION_STATE 編集順依存） |
| (c) 手動順 | DashboardData 構築時にカスタムソート設定 | ❌（運用負荷） |

→ **(a) 採用**。実装上は `sorted(self.data.milestones, key=lambda m: m.name)` 等で実現。

**ソート方式の明示（#NW4 対応）**:

- Wave 7 では **文字列辞書順（lexicographic order）** を採用する。Python の `str` 比較がそのまま使えるため実装最小、現在の Milestone 数（B-4 / B-5 の 2 件）では実害ゼロ。
- 制約: 将来 `B-10` 以降に到達すると `"B-10" < "B-4" < "B-5"` の順になる（数値直感と異なる）。
- 将来対応（Wave 8+）: Milestone 番号が `B-9` を超えた時点で **数値順ソートへの切替**を検討する（`sorted(..., key=lambda m: (m.name[0], int(m.name.split('-')[-1])))` 等の自然順実装）。
- 本 Wave 7 で数値順を採用しない理由: (1) 現状実装に該当ケースが存在しない、(2) 文字列辞書順から数値順への切替は後方互換破壊ではないため将来 Wave で安全に対応可能、(3) Wave 7 のスコープを「PoC 指摘パッケージ」に集中させるため。

---

## §4 Success Criteria

requirements.md §6 の AC-W7-1〜9 を満たすことで設計の成功とみなす。
追加の設計成功条件:

| 条件 | 確認方法 |
|:-----|:--------|
| 既存テスト退行ゼロ | Stage 1〜3 各 Stage 末で pytest 全件 PASS（NFR-W7-3） |
| 既存 V-2 動作の自然移行 | Wave 6 既存 V-2 テストが Stage 3 完了後も大半が PASS（緩和は L1 事前承認） |
| CSS 予算遵守 | Stage 3 設計段階で残予算（318 bytes）内に収まる根拠を本書 §7 で明記 |
| 後方互換 | Wave 6 終端時点の dashboard.html と比較し、`@` タグ無しの既存 task 表示が変化しない |

---

## §5 全体アーキテクチャ

### builder.py 改修ポイント

```
.claude/scripts/dashboard/builder.py（Wave 6 終端 610 行）
   ├─ TasksParser
   │    ├─ 行抽出 regex（厳格化 / Stage 1 改修）
   │    └─ Assignee タグ抽出（追加 / Stage 2 改修）
   ├─ DashboardBuilder
   │    ├─ V-2 ビュー生成（複数 Milestone 一覧化 / Stage 3 改修）
   │    ├─ V-4 ビュー生成（Assignee 列表示変更 / Stage 2 改修）
   │    └─ _render_filter_controls()（変更なし）
   └─ CSS 生成（Stage 3 で V-2 セクション分割用スタイル追加）
```

### データフロー

```
docs/specs/<milestone>/tasks.md（全 Milestone）
   ↓ TasksParser.parse()
TaskInfo[] （各 Task に assignee フィールド付き）
   ↓ DashboardBuilder.build()
HTML（V-2: Milestone セクション群 / V-4: Assignee 列表示済み）
```

### 影響範囲（モジュール一覧）

| モジュール | 改修内容 | Stage |
|:----------|:--------|:------|
| `TasksParser` | regex 厳格化 + Assignee 抽出 | Stage 1 / Stage 2 |
| `TaskInfo` データクラス | `assignee` フィールド追加 | Stage 2 |
| `DashboardBuilder.render_v2()` | 複数 Milestone セクション化 | Stage 3 |
| `DashboardBuilder.render_v4()` | Assignee 列表示変更 | Stage 2 |
| CSS（builder.py 内インライン） | V-2 セクション分割用スタイル | Stage 3 |
| 既存テスト | parser テスト群 + V-2 ビューテスト群 | Stage 1 / Stage 3（最小限の更新） |

---

## §6 Stage 1: TasksParser Task ID 抽出制約

### 改修ポイント

**現行（Wave 6 終端）**:
```python
TASK_ID_REGEX = r"^- \[([ x])\] (.+?):"
# → 「説明文:」のような行も Task として抽出してしまう
```

**Wave 7 Stage 1 改修後**:
```python
TASK_ID_REGEX = r"^- \[([ x])\] (W\d+(?:\.\d+)?-[A-Z]\d+-T\d+|T\d+):"
# → W7-B5-T44 / W1.5-B4-T9 / T99 形式のみ Task として抽出
# Wave 番号は整数 (W1, W7) と整数.5 (W1.5) の両方を許容（terminology.md §2 準拠）
```

**既存実装との整合**:

- 既存 `.claude/scripts/dashboard/parsers/tasks.py` の `_TASK_ID_PREFIX_RE` = `r"^(W\d+(?:\.\d+)?-[A-Za-z0-9]+-T\d+)"`
- Wave 番号部分（`W\d+(?:\.\d+)?`）は既存実装と一致
- Milestone 名部分は既存 `[A-Za-z0-9]+`（小文字許容）を本 Wave で `[A-Z]\d+`（大文字 + 数字に厳格化）にする
- これにより小文字混在の不正な Milestone 名（例: `b5`）は Wave 7 改修後に **抽出されなくなる**。terminology.md §2 で大文字 B + 数字が命名規約として明記されており、不正な小文字混在は実プロジェクトに存在しない想定（T44 影響分析で確認）

### 設計詳細

- 正規表現は **`re.match()` 相当（行頭固定）** で評価
- マッチしない行は **Task として抽出しない**（V-4 に出ない）
- マッチした場合の Task ID は capture group [2] から取得
- description は `:` 以降の文字列全体（既存挙動継続）

### Stage 1 完了時点の description における `@<assignee>` 文字列の扱い（#C-3 対応）

- Stage 1 の改修は **regex の Task 識別範囲のみ**であり、description の処理ロジックは変更しない
- 結果として `- [ ] W7-B5-T44: Task ID 厳格化 @Sonnet` のような行は、Stage 1 完了時点で `description = "Task ID 厳格化 @Sonnet"`（`@Sonnet` が文字列として残置）となる
- V-4 表示はそのまま `Task ID 厳格化 @Sonnet` が description カラムに出現する
- Stage 2 の `_extract_assignee()` 実装で description から `@Sonnet` が除去され、`description = "Task ID 厳格化"` + `assignee = "Sonnet"` に分離される
- **T46（既存テスト期待値更新）の前提**: Stage 1 完了時点の V-4 出力では description に `@<assignee>` を含むテキストがそのまま現れる。テストの期待値も `@<assignee>` を含む文字列として設定する。Stage 2 完了時点で再度期待値を更新する（T50 で対応）。

### Wave 7 全体の Task ID 採番との不整合チェック

- 本 Wave 7 タスク表の `T-S<stage>-<n>` 形式（例: `T-S1-1`）は厳格 regex `(W\d+-[A-Z]\d+-T\d+|T\d+)` にマッチしない（先頭が `T-S`、`T` の直後が `-` のためマッチしない）
- → **意図通り**: 検証タスクは TasksParser に拾われず、dashboard 上の Task としては表示されない（チェックリスト管理に閉じる）
- 通常タスク `W7-B5-T44` 等は正常にマッチし、V-4 に表示される

### エッジケース

| 行 | Wave 6 挙動 | Wave 7 挙動 |
|:--|:-----------|:-----------|
| `- [x] W1-B5-T1: 実装完了` | 抽出（id=`W1-B5-T1`） | 抽出（id=`W1-B5-T1`） |
| `- [x] W1.5-B4-T9: 波及修正` | 抽出（id=`W1.5-B4-T9`） | **抽出（id=`W1.5-B4-T9`）** ✅（Wave 1.5 維持） |
| `- [x] W10-B5-T100: 大規模タスク` | 抽出（id=`W10-B5-T100`） | 抽出（id=`W10-B5-T100`） ✅（Wave 二桁許容） |
| `- [x] T99: 単発タスク` | 抽出（id=`T99`） | 抽出（id=`T99`） |
| `- [x] 詳細: parser 強化` | **誤抽出**（id=`詳細`） | **抽出しない** ✅ |
| `- [ ] さらに具体的な手順を:` | **誤抽出**（id=`さらに具体的な手順を`） | **抽出しない** ✅ |
| `- [ ] W7-B5-T44: Task ID 厳格化 @Sonnet` | 抽出（id=`W7-B5-T44`） | 抽出（id=`W7-B5-T44`、assignee は Stage 2 で扱う） |

### Stage 1 既存テスト影響事前分析（L2 委譲ガードレール #4 適用）

| テストファイル | 想定影響 | 対応 |
|:--------------|:--------|:----|
| `test_tasks_parser*.py` | 厳格化 regex でテスト追加（誤抽出ゼロ化） | 追加（緩和なし） |
| `test_v4_view*.py` | 誤抽出行が消えるため期待件数の更新 | 期待値更新（L1 事前承認） |
| `test_dashboard_integration*.py` | 誤抽出行が消えるため検証行数の更新 | 期待値更新（L1 事前承認） |
| その他 | 影響なし想定 | Stage 1 末で全件 pytest 確認 |

### 実 tasks.md マッチ 0 件は Wave 7 仕様通り（v0.2.2 補追）

Wave 7 Stage 1 BUILDING 着手時の T45 実装後 pytest 検証で、実 docs/specs/ 配下の全 tasks.md チェックボックス行 600 件中、新 regex `^(W\d+(?:\.\d+)?-[A-Z]\d+-T\d+|T\d+):` にマッチする行が **0 件** であることが判明した（詳細: [2026-06-27-magi-wave7-stage1-pivot.md](../../../artifacts/2026-06-27-magi-wave7-stage1-pivot.md)）。

これは Wave 7 の正式目標（FR-W7-1 / AC-W7-1「誤抽出ゼロ化」）と整合した **仕様通りの挙動** である。V-4 Task 一覧の有用性は requirements.md §2 Goals に含まれず、Wave 8+ で別途設計予定。

**T46 への影響**:
- `test_parse_real_specs_directory_returns_at_least_one_task` テストは「実 specs から 0 件返却を許容」仕様に書き換える（または skip + reason 記録）
- `test_parse_checkbox_regex_matches_correct_pattern` (L275) は fixture を `W1-B5-T1` 等の正規形式に統一（既定承認 / T44 質問 1 対応）

**Wave 7 内での V-4 表示の確保**: NFR-W7-5（tasks.md パイロット運用 / requirements.md §5）により、Wave 7 tasks.md 自身を新規格 Task ID 行で構成する。詳細は本書 §10.5 を参照。

### 実装の追加要件（v0.2.3 / spec-critic 4 回目「見えない前提」Critical 反映）

spec-critic 4 回目レビューと実機確認で、現行 TasksParser の `_do_parse()` が `docs/specs/` 直下のみ非再帰走査することが判明（`.claude/scripts/dashboard/parsers/tasks.py` L73-L80）。これにより `docs/specs/b4-dashboard/wave7/tasks.md` は **走査対象外** であり、§3.5 パイロット運用が実装上機能しない（pytest `test_parse_real_specs_directory_returns_at_least_one_task` で実証）。

**Stage 1 スコープ拡張（T56 新規追加 / SE 級実装変更）**:

- `_do_parse()` の走査ロジックを `specs_dir.glob("**/tasks.md")` 再帰走査に変更
- `_extract_tasks()` で milestone_name 引数を廃止し、**Task ID（`W{n}-B{n}-T{n}`）の `B{n}` 部分から逆引きで `B-{n}` 形式の milestone を取得**
- Task ID が `T{n}` 単独形式の場合は milestone = ファイルパスから推測（fallback / 最も近い親ディレクトリ名）
- 既存 `docs/specs/b4-dashboard/tasks.md` / `goal-driven-orchestration/tasks.md` の走査挙動は維持（後方互換）

これにより `docs/specs/b4-dashboard/wave7/tasks.md` が走査対象となり、§3.5 のチェックボックス行が V-4 に表示可能になる。詳細は tasks.md §6 T56 を参照。

---

## §7 Stage 2: Assignee タグ規約の実装

### 元 design.md §5 への参照

**SSOT**: [元 design.md §5「Assignee タグ規約（Wave 7+ 追加 / RFC 2119 SHOULD）」](../design.md#assignee-タグ規約wave-7-追加--rfc-2119-should)

本書では §5 の再記述を行わない（MAGI Atom A4 確定方針）。
本 Stage の実装は **§5 の規約を文字通り具現化する** ことのみ。

### Stage 2 改修詳細

#### TasksParser の改修

```python
ASSIGNEE_REGEX = r"\s+@([A-Za-z0-9_-]+)\s*$"

def _extract_assignee(description: str) -> tuple[str, str]:
    """description 末尾から @<assignee> タグを抽出。
    戻り値: (clean_description, assignee) / 未マッチ時は (description, "-")
    """
    match = re.search(ASSIGNEE_REGEX, description)
    if match:
        assignee = match.group(1)
        clean = description[: match.start()].rstrip()
        return clean, assignee
    return description, "-"
```

**`re.search()` の `$` 挙動の注記（#W-2 対応）**:

- `re.search(r"\s+@([A-Za-z0-9_-]+)\s*$", description)` の `$` は **`re.MULTILINE` フラグを付けない場合、文字列末尾（または末尾の改行直前）にマッチ**する（Python 3 標準動作）
- description は TasksParser が `:` 以降を切り出した単一行文字列（改行を含まない想定）であるため、`$` は description の末尾を指す → 「行末固定」の意図と整合
- description 文中に途中 `@` を含む場合（例: `@L1 に報告済み @Sonnet`）でも、`\s+@([A-Za-z0-9_-]+)\s*$` は **末尾の `@Sonnet` のみ**にマッチする（中間の `@L1` は捕捉対象外）→ 元 design.md §5「タグは行末に 1 個まで。複数記載時は最後の 1 個のみ採用」と整合
- T50 のテストケースに **中間 `@` を含む description** を必ず含める（例: `description = "メール @example.com を更新 @Sonnet"` → `assignee="Sonnet"` / clean description は `@example.com` を保持）

#### `TaskInfo` データクラスへのフィールド追加

```python
@dataclass
class TaskInfo:
    id: str
    description: str
    status: TaskStatus
    milestone: str
    wave: Optional[str]
    assignee: str = "-"  # ← Wave 7 Stage 2 追加
```

#### V-4 ビュー出力

- 既存 Assignee 列の cell 値を `TaskInfo.assignee` に差し替え
- `-` 表示は従来通り
- `@` 接頭辞は parser 側で除去済み（V-4 では値そのまま表示）

### Stage 2 既存テスト影響事前分析

| テストファイル | 想定影響 | 対応 |
|:--------------|:--------|:----|
| `test_tasks_parser*.py` | Assignee 抽出テスト追加 | 追加（緩和なし） |
| `test_v4_view*.py` | Assignee 列の期待値更新 + `@<assignee>` タグ付きテストケース追加 | 期待値更新（L1 事前承認） |
| `test_dashboard_integration*.py` | 統合テストで Assignee 値出現を確認 | 追加検証 |

### tasks.md フォーマット運用ルール

Wave 7 以降の新規 tasks.md エントリには `@<assignee>` タグを **SHOULD** で記入する:
- 推奨値: `Sonnet`, `Haiku`, `Fable`, `Opus`, `human`
- 既存エントリへの遡及記入は **MAY**（強制しない）
- 詳細は元 design.md §5 を参照

---

## §8 Stage 3: 複数 Milestone 一覧化

### Milestone 識別の実装ベース定義（#C-1 / #C-2 対応）

**実装の SSOT**: `MilestoneInfo` は **`SessionStateParser` が SESSION_STATE.md 内の Task ID（`W{wave}-B{milestone_num}-T{task}` 形式）から逆引きで構築** する。`docs/specs/<dirname>/tasks.md` の glob 走査は **使われていない**（元 design.md §5 と実装の乖離 / 既存仕様ドリフト / 別タスクで対応）。

- `MilestoneInfo` フィールド:
  - `name: str`（例: `B-5` / SESSION_STATE 内 Task ID の `B<n>` から構築）
  - `current_step: str`（SessionStateParser 段階では `"UNKNOWN"` / **DashboardBuilder 側で `self.data.current_phase` に上書きされ全 Milestone 共通の値が表示される**）
  - `status: str`（"in-progress" 等）
- 結果として **Step は全 Milestone 共通**（current_phase 単一値）が現状仕様。Wave 7 ではこれを維持し、Milestone 別 Step 管理は将来候補（chip `task_68008f88` 関連）。

### V-2 検出される Milestone 件数の前提

- SessionStateParser は SESSION_STATE.md の Task ID 群から Milestone を逆引き
- 現状 SESSION_STATE.md は `W{n}-B5-T{n}` 系の Task ID が大半（B-5 単独 Milestone 状態）
- AC-W7-4「2 件以上の Milestone 表示」達成のためには、SESSION_STATE.md に複数 Milestone を参照する Task ID が記述されていること（requirements.md FR-W7-4 補足の通り）
- Stage 4 の T-S4-7 でユーザー確認時に必要なら SESSION_STATE.md に検証用 Task ID 行を追加する（運用作業）

### HTML 構造設計

V-2 ビューの構造を「単一エントリ表示」から「Milestone セクション群」に拡張:

```html
<section id="v2-milestones">
  <h2>Milestone 一覧</h2>
  <div class="milestones-container">
    <!-- ↓ for ms in self.data.milestones の動的生成 -->
    <article class="milestone-card" data-milestone="{ms.name}">
      <h3>{ms.name}</h3>
      <p>Step: <span class="step">{self.data.current_phase}</span></p>
      <p>状態: <span class="status">{ms.status}</span></p>
    </article>
    <!-- ↑ Milestone 件数分繰り返し -->
  </div>
</section>
```

**例（実行時の出力 / 現状 SESSION_STATE で 1 Milestone の場合）**:

```html
<div class="milestones-container">
  <article class="milestone-card" data-milestone="B-5">
    <h3>B-5</h3>
    <p>Step: <span class="step">PLANNING</span></p>
    <p>状態: <span class="status">in-progress</span></p>
  </article>
</div>
```

**例（SESSION_STATE に B-4 と B-5 の Task ID を含む場合）**:

```html
<div class="milestones-container">
  <article class="milestone-card" data-milestone="B-4">
    <h3>B-4</h3>
    <p>Step: <span class="step">PLANNING</span></p>  <!-- 全 Milestone 共通 / current_phase -->
    <p>状態: <span class="status">in-progress</span></p>
  </article>
  <article class="milestone-card" data-milestone="B-5">
    <h3>B-5</h3>
    <p>Step: <span class="step">PLANNING</span></p>  <!-- 同上 / 共通 -->
    <p>状態: <span class="status">in-progress</span></p>
  </article>
</div>
```

### CSS 設計（V-2 セクション拡張）

```css
.milestones-container {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.milestone-card {
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 0.75rem 1rem;
  background: var(--color-surface);
}

.milestone-card h3 {
  margin: 0 0 0.25rem 0;
  font-size: 1.1rem;
  color: var(--color-text-strong);
}
```

### CSS 予算事前評価（NFR-W7-1 対応）

| 項目 | 推定 bytes |
|:-----|:----------|
| `.milestones-container` ルール | ~80 |
| `.milestone-card` ルール | ~140 |
| `.milestone-card h3` ルール | ~80 |
| **小計** | **~300 bytes** |

Wave 6 終端時点 9,922 bytes + 追加 300 bytes ≈ **10,222 bytes**（上限 10,240 / 残 18 bytes）

→ ギリギリ収まる見込み。**Stage 3 実装時に L2 から実測値を都度報告させる**。

万一超過した場合の縮退オプション（#W-1 対応 / 各オプションの節約効果見積もり付き）:

| Opt | 内容 | 節約効果（推定） | 採用優先度 |
|:---:|:----|:---------------|:----------|
| 1 | `gap: 0.75rem;` を既存 CSS 変数（例: `--spacing-md`）で共有化 → 1 行削減 | ~30 bytes | 高（影響小） |
| 2 | `.milestone-card { padding: 0.75rem 1rem; }` を `padding: 0.5rem;` に圧縮 | ~10 bytes（バイト効果は小 / 視覚効果も小） | 中 |
| 3 | `.milestone-card h3` のスタイル（`margin: 0 0 0.25rem 0; font-size: 1.1rem;`）を既存 `h3` ベース共通スタイルに集約 | ~80 bytes | 高（最大効果） |
| 4 | `<p>状態: <span class="status">{ms.status}</span></p>` を `<p class="milestone-status">状態: {ms.status}</p>` に変更し、`.status` 専用クラスをまったく設けない。スタイルは `.milestone-card p` の共通ルールに集約 | ~50 bytes（CSS 共通化分） | 低（HTML 構造変化リスク） |

**3 件すべて適用時の節約**: ~30 + ~10 + ~80 = **~120 bytes**（残予算 18 + 120 = 138 bytes の余裕に拡大）

**それでも超過する場合の最終判断（PM 級）**: Stage 3 のスコープから「`.milestone-card h3` の意匠カスタマイズ」を削除し、Wave 8+ へ送る。本判断は L1 から PM（ユーザー）にエスカレーション。

**縮退オプション適用の権限等級（v0.2.3 / spec-critic 4 回目 Warning 5 対応）**:

- **Opt 1 / Opt 2**（節約効果 < 30 bytes）: **SE 級** — L2 が自律適用可（完了報告で明示）
- **Opt 3**（節約効果 ~80 bytes / 既存 h3 共通スタイルへの集約）: **PM 級** — 既存スタイルへの影響あり / L1 経由で PM 承認後に適用
- **Opt 4**（HTML 構造変化 / `.status` クラス廃止）: **PM 級** — 公開 HTML 構造変更 / 同上
- **3 件以上を組み合わせて適用する場合**: **PM 級** — 副作用の組み合わせ評価が必要

### Stage 3 既存テスト影響事前分析

| テストファイル | 想定影響 | 対応 |
|:--------------|:--------|:----|
| `test_v2_view*.py` | 単一 Milestone 想定のテストが複数 Milestone 想定に変わる | 大幅期待値更新（L1 事前承認 / **Wave 7 で最も影響範囲大**） |
| `test_dashboard_integration*.py` | 複数 Milestone 出現検証追加 | 追加検証 |
| `test_wave6_stage1_css.py` | CSS 上限テストは継続有効 | 継続 |

### Future-Proof: フィルタ後方互換性

Wave 8+ で option 2（フィルタトグル）を追加する場合に備え:
- `data-milestone` 属性を各 `.milestone-card` に付与（JS から識別可能）
- 表示状態は CSS class（例: `.milestone-card--hidden`）で制御する設計
- 現 Wave では JS フィルタ実装はしないが、属性は付ける

---

## §9 Stage 4: 統合テスト + Lighthouse + PoC レビュー

Wave 6 Stage 4 のパターンを踏襲:

| Task | 内容 |
|:-----|:----|
| 統合テスト | `test_wave7_integration.py` 新設 / 9 件想定（Stage 1〜3 横断検証） |
| Lighthouse 計測 | snapshot モード / Accessibility ≥ 95 確認（AC-W7-6） |
| pytest 全件 | NFR-W7-3 達成確認 |
| CSS サイズ実測 | 10,240 bytes 以下確認（AC-W7-5） |
| ユーザー PoC レビュー | dashboard.html 提示 + 主観評価 OK（AC-W7-9） |
| Wave 7 final status | retro 起動 + COMPLETE 宣言 |

統合テストの内訳（Wave 6 Stage 4 パターン踏襲）:
- 静的検証 4 件（HTML サイズ / CSS サイズ / 外部参照 regex / Milestone 件数）
- MCP skip 5 件（chrome-devtools-mcp 駆動 / 疑似コード残置 + L1 実機検証）

---

## §10 既存テスト影響事前分析（横断サマリ）

L2 委譲ガードレール #4「既存テスト影響事前分析」を Stage 委譲時に明示する。
本書 §6〜§8 で Stage 別に詳細記載済。横断サマリ:

| Stage | 影響テストファイル | 緩和必要性 |
|:------|:------------------|:----------|
| Stage 1 | `test_tasks_parser*.py` 追加 / `test_v4_view*.py` 期待値更新 / `test_dashboard_integration*.py` | 軽度（期待値更新のみ） |
| Stage 2 | `test_tasks_parser*.py` 追加 / `test_v4_view*.py` 期待値更新 + ケース追加 / `test_dashboard_integration*.py` | 軽度〜中（ケース追加） |
| Stage 3 | `test_v2_view*.py` 期待値大幅更新（**Wave 7 で最も影響範囲大**） | 中〜重（L1 事前承認必須） |
| Stage 4 | 新規 `test_wave7_integration.py`（9 件想定） | 既存影響なし |

---

## §10.5 tasks.md パイロット運用ルール（v0.2.2 補追）

Wave 7 Stage 1 MAGI 合議（[2026-06-27-magi-wave7-stage1-pivot.md](../../../artifacts/2026-06-27-magi-wave7-stage1-pivot.md)）で確定したパイロット運用の設計仕様。requirements.md §5 NFR-W7-5 と連動。

### 運用ルール（SHOULD）

| 対象 | 記法 | TasksParser 抽出 |
|:-----|:-----|:----------------:|
| Wave 7 実装タスク（T44-T55） | `- [ ] W7-B5-T44: 既存テスト構造変更影響分析 @sonnet` | ✅ |
| Wave 7 検証タスク（T-S*） | `- [ ] **T-S1-1**: pytest 全件 PASS` | ❌（design.md §2 維持） |
| Wave 6 以前 tasks.md | 旧表記維持（書き換え不要） | terminology.md §5 移行猶予条項適用 |

### 設計上の制約

- パイロット運用は **Wave 7 tasks.md のみ** を対象（限定スコープ）
- 既存表形式と並存可（表 + チェックボックスの二重管理 / MAY）
- Assignee タグ `@sonnet` / `@haiku` 等は SHOULD（元 design.md §5 規約準拠）

### Stage 2 AC-W7-3 達成の前提（v0.2.3 / Critical 1 解消）

AC-W7-3 達成には以下の **全 4 条件** がすべて満たされる必要がある（spec-critic 4 回目 Critical 1 指摘反映 / 達成依存チェーン明示）:

| 前提 | 担当タスク | Stage |
|:-----|:---------|:------|
| 1. TasksParser がディレクトリ再帰走査で wave7/tasks.md を読む | T56 | Stage 1 |
| 2. Wave 7 tasks.md §3.5 に新規格 Task ID 行 + `@<assignee>` タグが記述されている | §3.5（v0.2.2 で導入済） | (補追済) |
| 3. TaskInfo に assignee フィールドが存在する | T47 | Stage 2 |
| 4. TasksParser に `_extract_assignee()` が実装されている + V-4 が `TaskInfo.assignee` を表示 | T48 + T49 | Stage 2 |

**Stage 1 完了時点**: 前提 1 + 2 のみ達成（前提 3 + 4 が未実装のため、V-4 Assignee 列は `"-"` 固定のまま）。
**Stage 2 完了時点**: 前提 4 まで達成 → AC-W7-3 達成可能（V-4 Assignee に `sonnet` 等の値が ≥ 1 件表示）。

**いずれか 1 つでも未達なら AC-W7-3 達成不能**。Stage 1〜2 のゲート判断で各前提の達成を逐一確認する。

### Wave 8+ への送り

- 全 tasks.md（17 ファイル / 600 行）の新規格統一は Wave 8+ で別 Milestone として扱う
- 移行猶予条項の終了タイミングは Wave 8+ で再評価
- V-4 表示の有用性（Task 一覧の意味化）は Wave 8+ で本格設計

---

## §11 upstream-first 裏取りステータス

| 対象 | 確認 | 備考 |
|:-----|:----|:----|
| Python `re` 正規表現の `^W\d+-[A-Z]\d+-T\d+$` | ✅ | 既存 SessionStateParser で同種 regex を使用中 |
| `\s+@([A-Za-z0-9_-]+)\s*$` | ✅ | 元 design.md §5 で承認済（commit `4448d4c`） |
| `@dataclass` フィールド追加（`assignee: str = "-"`） | ✅ | Python 3.11 標準 |
| Lighthouse snapshot モード（file:// URL） | ✅ | Wave 6 Stage 4 で実証（97 / 100 / 60 / 50） |
| chrome-devtools-mcp `lighthouse_audit` | ✅ | Wave 5/6 で利用実績あり |

---

## §12 改訂履歴

| バージョン | 日付 | 変更内容 |
|:----------|:-----|:--------|
| 0.1.0 | 2026-06-27 | 初版起稿 — Wave 7 requirements.md v0.1.0 (Approved) + MAGI 合議 (2026-06-27) に基づく設計 |
| 0.2.0 | 2026-06-27 | spec-critic 独立レビュー指摘の反映 — §6 Stage 1 description 挙動明記 (#C-3) / §7 re.search 注記 (#W-2) / §8 Milestone 識別実装ベース定義 + HTML 例動的生成形 + Step 共通明示 (#C-1 / #C-2 / #I-1) / §8 縮退効果量見積もり (#W-1) / ステータス Conditional Approved (#C-4) |
| 0.2.0+1 | 2026-06-27 | spec-critic 再レビュー（v0.2.0 → B 評価）指摘のインライン補記 — §8 Opt 4 表記修正（`.status` クラス未定義問題解消 / #NI-1）/ §14 参照を requirements.md v0.2.0 に更新 |
| **0.2.1** | 2026-06-27 | spec-critic 再々レビュー（v0.2.0+1 → B 維持）指摘の追加補記 + バージョン正式 bump — §6 regex を Wave 1.5 形式 `W\d+(?:\.\d+)?-[A-Z]\d+-T\d+` に拡張 + 既存実装との整合明記 + エッジケース表に Wave 1.5 / W10 追加（**継続懸念解消**）/ §3 A3-4 にソート方式（文字列辞書順）+ 将来 (B-10 以降の数値順) 切替方針明示 (#NW4) / §14 参照を requirements.md v0.2.1 に更新 |
| **0.2.2** | 2026-06-27 | Wave 7 Stage 1 BUILDING 着手時の構造的乖離発覚に対する MAGI 合議結果反映 — §6 末尾に「実 tasks.md マッチ 0 件は Wave 7 仕様通り」補足追加 + T46 への影響明記 / §10.5（新規）tasks.md パイロット運用ルール追加 / §13 に v0.2.2 PM 補追承認記録 / 根拠議事録: `2026-06-27-magi-wave7-stage1-pivot.md` |
| **0.2.3** | 2026-06-27 | spec-critic 4 回目レビュー指摘の反映 — §6 に「実装の追加要件」追加（T56 ディレクトリ再帰走査 / Critical 昇格対応）/ §10.5「Stage 2 AC-W7-3 達成の前提」を 4 条件依存チェーンに展開（Critical 1 解消）/ §8 CSS 縮退オプション権限等級明示（Warning 5）/ §13 に v0.2.3 PM 補追承認記録 / §14 参照を requirements.md v0.2.3 に更新 |

---

## §13 PM 承認記録

### 2026-06-27: v0.2.2 PM 補追承認（Wave 7 Stage 1 MAGI Pivot 反映）

Wave 7 Stage 1 BUILDING 着手時に T45 実装後の pytest 検証で発覚した「design.md §6 新 regex 仕様と実 tasks.md 運用の構造的乖離」に対し、MAGI 合議（[2026-06-27-magi-wave7-stage1-pivot.md](../../../artifacts/2026-06-27-magi-wave7-stage1-pivot.md)）で確定した A 案（スコープ縮小）+ Wave 7 tasks.md パイロット運用方針を本書に補追。具体的な追加内容:

- §6 末尾「実 tasks.md マッチ 0 件は Wave 7 仕様通り」補足
- §10.5（新規）「tasks.md パイロット運用ルール」セクション
- ステータスを v0.2.2 Approved（PM 補追承認）に更新

requirements.md / tasks.md にも v0.2.2 で連動補追。

### 2026-06-27: v0.2.3 PM 補追承認（spec-critic 4 回目レビュー反映）

v0.2.2 補追を spec-critic 4 回目に独立レビューさせた結果、Critical 3 件（うち 1 件は L1 実機確認で昇格）+ Warning 4 件 + Info 3 件の指摘を受領。指摘と対処マッピング:

| spec-critic 指摘 | 重要度 | 対処（v0.2.3） |
|:----------------|:------|:--------------|
| 見えない前提: TasksParser 非再帰走査で wave7/tasks.md 読まれず | Critical 昇格（実機確認） | §6「実装の追加要件」追加 + tasks.md T56 新規追加 |
| AC-W7-3 達成依存チェーン未明示 | Critical 1 | §10.5「Stage 2 AC-W7-3 達成の前提」を 4 条件展開 |
| Stage 3 ゲートと AC-W7-4 矛盾 | Critical 2 | tasks.md T-S3-4 / Stage 3 ゲート条件に conditional pass 基準追記 |
| T46 仕様乖離（pytest 結果確認の追加） | Warning 3 | tasks.md §6 T46 完了条件に pytest 事前確認追加 |
| NFR-W7-5 SHOULD vs AC-W7-3 MUST 矛盾 | Warning 2 | requirements.md NFR-W7-5 を MUST 昇格 |
| §3 / §3.5 二重管理の同期ルール未定義 | Warning 4 | tasks.md §3.5 補追注記に同期ルール明示 |
| CSS 縮退オプション権限等級未定 | Warning 5 | §8 縮退オプション 4 件に権限等級表追加 |
| T55 `@human` と §3「L1 + human」表記対応 | Info 1 | tasks.md §3.5 補追注記 |
| §14 参照リスト v0.2.1 のまま | Info 2 | §14 を v0.2.3 に更新 |
| §10 §9 承認記録の視点差 | Info 3 | 視点差は許容（個別文書からの主体記述）|

ステータスを v0.2.3 Approved（PM 補追承認）に更新。requirements.md / tasks.md にも v0.2.3 で連動補追。

### 2026-06-27: 3 文書セット v0.2.1 PM 最終承認

ユーザー（PM）が requirements.md v0.2.1 + design.md v0.2.1 + tasks.md v0.2.1 の 3 文書セットを一括承認。
spec-critic 3 回独立レビュー結果（C → B → B → A 想定）を反映済。BUILDING フェーズ遷移可。

### 2026-06-27: design.md v0.1.0 承認

PM（ユーザー）が本設計書 v0.1.0 を Approved。tasks.md 起稿に進行。

### 2026-06-27: spec-critic 独立レビュー結果（v0.2.0 改訂 / Conditional Approved）

spec-critic から Critical 4 件 / Warning 6 件 / Info 4 件 / 総合 C 評価の指摘を受領。
本設計書への反映項目:

- #C-1（Milestone 識別の前提崩壊）→ §8 に「Milestone 識別の実装ベース定義」追加、HTML 例から固有 Step 値（B-3=AUDITING 等）削除、SessionStateParser ベースに整合
- #C-2（V-2 Step 表示のデータソース）→ §8 に「Step は全 Milestone 共通（current_phase）」明示
- #C-3（Stage 1 description 挙動）→ §6 に「Stage 1 完了時点では description に `@<assignee>` 文字列残置」明記
- #C-4（承認ステータス不整合）→ Conditional Approved に変更、3 文書セット PM 最終承認待ち
- #W-1（CSS 縮退効果量）→ §8 縮退オプション 4 件に節約効果見積もり追加（合計 ~120 bytes）
- #W-2（re.search + $ 挙動）→ §7 に Python 3 標準動作の注記 + 中間 `@` を含むテストケース指示
- #I-1（HTML 例ハードコード）→ §8 HTML 例を `for ms in self.data.milestones` の動的生成形に修正

tasks.md にも v0.2.0 改訂で連動。3 文書セットでの PM 最終承認を依頼。

---

## §14 参照

- [Wave 7 requirements.md](requirements.md) v0.2.3 Approved
- [元 design.md §5 Assignee タグ規約](../design.md#assignee-タグ規約wave-7-追加--rfc-2119-should)
- [MAGI 議事録 2026-06-27](../../../artifacts/2026-06-27-magi-wave7-planning.md)
- [retro Wave 6](../../../artifacts/retro-W6-B5-2026-06-27.md)
- [L2 委譲ガードレール](../../../artifacts/knowledge/l2-delegation-guardrails.md)
