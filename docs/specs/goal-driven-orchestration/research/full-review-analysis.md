# full-review 現仕様分析・改造見積もり

**作成日**: 2026-06-11
**対象スキル**: `.claude/skills/full-review/SKILL.md` (version 1.0.0)
**目的**: B-3 ゴール駆動オーケストレーション FR-9 / AC-14 対応。改造着手前の PM 提出資料。
**ステータス**: Draft（PM 承認待ち）

---

## 1. 現仕様の構造

### 1.1 ステージ構成

| Stage | 名称 | 実行条件 | 主入力 | 主出力 |
|-------|------|---------|-------|-------|
| 0 | 初期化 | 常に実行 | 引数（対象パス） | `lam-loop-state.json`、`scale-detection.json` |
| 1 | 静的解析 + 依存グラフ構築 | Plan A 以上の場合のみ | `scale-detection.json` | `static-issues.json`、`summary.md` |
| 2 | チャンク分割 + 並列監査 | 常に実行（モード分岐あり） | `static-issues.json`（任意） | `file-cards/`、`contracts/`、監査レポート |
| 3 | 階層的統合 + レポート生成 | 常に実行（Layer 2/3 は Plan C 以上） | `file-cards/`、`contracts/` | 統合レポート（`audit-reports/YYYY-MM-DD-iterN.md`）、`layer3-issues.json` |
| 4 | トポロジカル順修正 | 常に実行 | 統合レポート | 修正済みコード |
| 5 | 検証 + Green State 判定 + 完了 | 常に実行 | テスト結果、`lam-loop-state.json` | Green State 判定、ループログ |

**ループ制御**: Stage 5 完了後、Claude が自律的に Stage 2 へ戻る。`lam-loop-state.json` の `active` フラグで管理。`lam-stop-hook.py` は安全ネット（ブロック）のみ担う。

### 1.2 状態ファイル

| ファイルパス | 役割 | 書き手 | 読み手 |
|------------|------|-------|-------|
| `.claude/lam-loop-state.json` | ループ管理（active/iteration/max_iterations/pm_pending/fullscan_pending/tool_events） | /full-review（Claude） + PostToolUse hook | lam-stop-hook.py + Claude |
| `.claude/review-state/scale-detection.json` | Scale Detection 結果（Plan A〜D） | Stage 0 `scale_detector.py` | Stage 1〜4 |
| `.claude/review-state/static-issues.json` | 静的解析 Issue リスト | Stage 1 `run_pipeline.py` | Stage 2〜3 |
| `.claude/review-state/summary.md` | LLM 向けサマリー | Stage 1 `run_pipeline.py` | Stage 2 Agent プロンプト |
| `.claude/review-state/chunks.json` | チャンク一覧（Plan B 時のみ） | Stage 2 `chunker.py` | Stage 2 並列 Agent |
| `.claude/review-state/file-cards/` | ファイル概要カード | Stage 2 Agent 出力 + `card_generator.py` | Stage 3 |
| `.claude/review-state/contracts/` | モジュール契約カード | Stage 3 `merge_contracts()` | Stage 2（次イテレーション注入） |
| `docs/artifacts/audit-reports/YYYY-MM-DD-iterN.md` | 統合監査レポート（永続） | Stage 3 | 人間・次イテレーション |
| `.claude/logs/loop-YYYYMMDD-HHMMSS.txt` | ループ終了ログ | lam-stop-hook.py または Claude | 人間・レトロ |

### 1.3 サブエージェント構成（Stage 2）

Stage 2 で以下のサブエージェントを並列起動する:

- `code-reviewer` (1): ソースコード品質
- `code-reviewer` (2): テストコード品質
- `quality-auditor`: アーキテクチャ・仕様整合性
- `code-reviewer` (3): セキュリティ（OWASP Top 10）

### 1.4 外部依存・前提条件

| 前提 | 内容 |
|------|------|
| トップレベル実行前提 | Stage 0 Step 1 でプロジェクトルートを `.` として `lam-loop-state.json` を生成。サブエージェント内ではカレントディレクトリが変わる可能性がある |
| gitleaks | 未インストール時は `gitleaks:not-installed` Critical Issue が生成され G5 FAIL |
| ruff / bandit | 未インストール時は `ToolNotFoundError`。Stage 1 中止（Stage 2 以降は続行可） |
| tree-sitter | 未インストール時は AST チャンキングが非活性化（従来モードへ自動フォールバック） |
| python3 | `.claude/hooks/analyzers/` のスクリプト実行に必要 |
| `run_phase0()` に project_root を渡す | サブパス渡しは `<サブパス>/.claude/review-state/` に誤った場所へ永続化（既知 W2-P2 ノート） |
| ユーザー対話が必要な箇所 | Stage 0 Step 4（untracked ファイル確認）、Stage 3（修正方針承認）、Stage 4 PM 級処理 |

### 1.5 トップレベル実行前提の箇所（改造 (a) で特に注意が必要な箇所）

1. **Stage 0 Step 1**: `lam-loop-state.json` の生成に `$TARGET` と `$TIMESTAMP` のシェル変数展開を使用するヒアドキュメント形式。サブエージェントではカレントディレクトリが変わる可能性。
2. **`lam-stop-hook.py`**: `get_project_root()` でプロジェクトルートを取得し `lam-loop-state.json` を参照。サブエージェントから呼び出された場合に `stop_hook_active` フラグの管理が競合する。
3. **State ファイルのパス固定**: 全 Stage が `.claude/lam-loop-state.json`、`.claude/review-state/` という固定パスに読み書きする。複数インスタンスが同時実行された場合にパス競合が発生する。
4. **Stage 3 ユーザー承認**: 統合レポート提示後、修正方針の承認を対話的に求める（`修正に進みますか？（承認 / 一部除外 / 中止）`）。サブエージェント内では人間への対話不可。
5. **Stage 4 PM 級停止**: PM 級 Issue 発見時に `pm_pending=true` をセットして応答終了し、ユーザー判断を待つ。サブエージェント内では上位層への伝達が必要。

---

## 2. 改造 (a) の分析 — サブエージェント呼び出し化

### 2.1 必要な変更点の列挙

| # | 変更箇所 | 変更内容 | 影響度 |
|---|---------|---------|-------|
| A-1 | Stage 0 Step 1 の状態ファイル生成 | ターゲットパスとタイムスタンプを引数経由で受け取るよう、シェル変数依存を排除。実行 ID（`invocation_id`）を生成し、状態ファイル名をインスタンス固有化（例: `lam-loop-state-<id>.json`）する | M |
| A-2 | 状態ファイルのパス管理 | 全 Stage の `lam-loop-state.json` 参照を `invocation_id` ベースのパスに変更。あるいは `review-state/<invocation_id>/` というサブディレクトリに全状態ファイルを収容 | L |
| A-3 | `lam-stop-hook.py` のインスタンス識別 | 複数インスタンスが同時実行された場合、Stop hook がどの `lam-loop-state.json` を参照するかを `agent_id` 等で識別する仕組みを追加する | M |
| A-4 | ユーザー対話の除去または上位委譲 | Stage 0 Step 4（untracked 確認）、Stage 3（修正方針承認）をパラメータ化（例: `auto_approve: bool`）し、サブエージェントモードでは人間への問い合わせをスキップまたは上位層への構造化報告に変換する | M |
| A-5 | PM 級 Issue の上位報告 | Stage 4 PM 級処理の「応答終了してユーザー待ち」をサブエージェントモードでは「構造化レポートを返して終了」に変換する | S |
| A-6 | `run_phase0()` への project_root 渡しの保証 | サブエージェント呼び出し時のカレントディレクトリ変動に対して、project_root を明示引数として全 `python3 -c` 呼び出しに渡す（既知の W2-P2 運用知見の汎化） | S |
| A-7 | SKILL.md フロントマターへの引数定義追加 | `disable-model-invocation: true` は維持。`argument-hint` に `invocation_id`、`auto_approve`、`rubric_path`（改造(b)と共通）を追加定義 | S |

### 2.2 互換性影響（既存トップレベル用途）

| 項目 | 影響 | 対策 |
|------|------|------|
| A-1〜A-3 の状態ファイル変更 | `invocation_id` を省略した場合は従来のパス（`lam-loop-state.json`）にフォールバックすれば後方互換を維持できる | オプション引数として `invocation_id` を追加し、未指定時は従来パスを使用 |
| A-4 の対話除去 | `auto_approve=false`（デフォルト）時は従来通り人間への問い合わせを継続 | フラグのデフォルト値で分岐 |
| A-5 の PM 級報告変換 | サブエージェントモード引数が未指定（デフォルト false）の場合は従来通り応答終了で人間待ち | 同上 |
| `lam-stop-hook.py` の変更 | 単一インスタンスのトップレベル実行では `invocation_id` が未指定のため従来通り動作 | ID 未指定時の後方互換パスを維持 |

**結論**: A-1〜A-7 をオプション引数・フォールバック設計で実装すれば、既存のトップレベル用途は完全に維持できる。破壊的変更は不要。

---

## 3. 改造 (b) の分析 — rubric ファイル入力

### 3.1 rubric ファイルの受け口設計案

**受け口の候補**:

| 案 | 方式 | メリット | デメリット |
|----|------|---------|-----------|
| b-1 | SKILL.md フロントマターの引数に `rubric_path` を追加し、Stage 0 で読み込んで状態ファイルに格納 | 最小変更。既存の引数渡し機構を流用 | 状態ファイル経由なので各 Stage がパスを意識する必要あり |
| b-2 | Stage 2 の各 Agent プロンプトに rubric.md の内容を直接注入するオプションを追加 | Agent が rubric の全項目を直接参照できる | プロンプトが肥大化。大規模 rubric では非効率 |
| b-3 | Stage 3 のレポート統合時に rubric 項目との照合セクションを追加 | Green State 判定と rubric 照合を一体化できる | Stage 3 の変更量が大きい |

**推奨**: b-1 + b-2 の組み合わせ。`rubric_path` を Stage 0 で受け取り、状態ファイルに格納。Stage 2 Agent プロンプトには要約版のみ注入（フル内容はファイルパス参照）。

### 3.2 既存 Green State 判定との関係

現行の Green State 条件（G1〜G5）と rubric 照合の位置付けは以下の通り:

```
現行 Green State: Critical=0 かつ Warning=0 (G3) + G1/G2/G4/G5 通過
rubric 照合: 「rubric の全項目が合格」という追加条件
```

rubric 照合は G3〜G5 の後に来る **G6（rubric 整合性）** として位置付けるか、または Stage 5 の Green State 判定に rubric_path が指定されている場合の追加チェックとして実装するのが最小変更。

**重要**: rubric は「仕様・品質基準」ではなく「タスクゴール条件」の役割を持つ。G1〜G5 は LAM 固有の品質定義であり、rubric はそれに加えてゴール駆動オーケストレーションが設定したタスク固有の合否条件を表す。両者は**and 条件**（どちらも満たして初めて Green State）として設計すべきである。

### 3.3 rubric 照合の実装位置

| 位置 | 適切性 | 理由 |
|------|-------|------|
| Stage 2（Agent プロンプトに注入） | 一部適切 | Agent が rubric 観点でレビューできる。ただし全 Stage で重複注入が必要になる |
| Stage 3（レポート統合時に rubric 対比セクションを追加） | 適切 | Issue 統合後に rubric 項目との照合を一括で行える |
| Stage 5（Green State 判定時に rubric_pass チェックを追加） | 最適 | 最終 G6 として一か所に集約。実装コストが低い |

**推奨**: Stage 5 で `rubric_path` が指定されている場合に G6 チェックを追加する最小変更案。rubric 項目の詳細照合は grader エージェント（B-3 新スキル側）が担う設計とし、full-review は「合格/不合格/保留」を返す簡易インターフェースを提供する。

---

## 4. 工数見積もり

### 4.1 改造 (a) — サブエージェント呼び出し化

| タスク | 規模 | 根拠 |
|-------|------|------|
| A-1: `invocation_id` 導入と状態ファイル名変更 | S | Stage 0 の JSON 生成箇所のみ変更。パス文字列置換が主 |
| A-2: 全 Stage の状態ファイルパス参照変更 | M | SKILL.md 内の全 Stage で `lam-loop-state.json` の参照が多数。5〜10 箇所の `python3 -c` コマンドを修正 |
| A-3: `lam-stop-hook.py` のインスタンス識別 | M | `agent_id` によるインスタンス特定ロジックの追加。Python コードの変更で既存テストへの影響あり。テスト追加も要 |
| A-4: 対話除去 / 上位委譲（`auto_approve` 引数追加） | S | Stage 0 Step 4 と Stage 3 の問い合わせ箇所に `auto_approve` 分岐を追加 |
| A-5: PM 級の構造化報告変換 | S | Stage 4 Step 2 に `subagent_mode` 分岐を追加 |
| A-6: `run_phase0()` project_root 保証 | S（変更は軽微だが注意深い検証が必要） | 既存の動作知見（W2-P2）の汎化。誤ると junk ファイル生成の再現リスクあり |
| A-7: フロントマター引数定義 | S | SKILL.md の冒頭数行のみ |
| **合計** | **M〜L** | コアの状態ファイル競合対処（A-2/A-3）が複数ファイルをまたぐため M 相当。テスト追加含めると L に近づく |

**タスク数見積もり**: 7 タスク（A-1〜A-7）。実装 2〜3 セッション + テスト 1 セッション + 統合確認 1 セッション。

### 4.2 改造 (b) — rubric ファイル入力

| タスク | 規模 | 根拠 |
|-------|------|------|
| B-1: SKILL.md フロントマターへの `rubric_path` 引数追加 | S | 1 行の変更 |
| B-2: Stage 0 での `rubric_path` 読み込みと状態ファイルへの格納 | S | Stage 0 Step 1 の JSON スキーマに `rubric_path` フィールドを追加 |
| B-3: Stage 5 への G6（rubric_pass）チェック追加 | S〜M | G5 のチェックに類似した構造。rubric の各項目を別 grader に渡す軽量設計か、全文参照の重い設計かで規模が変わる |
| B-4: Stage 2 Agent プロンプトへの rubric 要約注入（オプション） | S | プロンプト生成箇所への数行の追記 |
| **合計** | **S〜M** | B-3 を「grader に委譲する軽量インターフェース」として実装すれば S。full-review 内で rubric 全照合を実装すると M |

**タスク数見積もり**: 4 タスク（B-1〜B-4）。実装 1 セッション + 確認 0.5 セッション。

### 4.3 段階的実施案（最小改造で先行できる範囲）

**フェーズ 1（先行・最小コスト）**: B-1 + B-2 + B-4 のみ実施。  
rubric_path を受け取る「受け口だけ」を用意し、Stage 2 Agent プロンプトに rubric 内容を注入する。  
G6 判定は実装せず、rubric 照合は grader（B-3 新スキル側）が単独で行う。  
工数: S（1 セッション以内）。後方互換完全維持。

**フェーズ 2（改造 (a) コア）**: A-1 + A-4 + A-5 + A-7 のみ実施。  
`invocation_id` なしの「引数だけ増やす」最小変更。状態ファイル競合は発生しないため並列実行不可だが、直列呼び出しには対応可能。  
工数: S〜M（1〜2 セッション）。

> **注**: A-6（`run_phase0()` への `project_root` 渡し）は本来フェーズ 3 構成要素だが、フェーズ 2 でサブエージェント直列呼び出しを実装した時点で R-3（W2-P2 系パスバグ）が顕在化するため、フェーズ 2 着手時に **前提条件として前倒し実施** すること。§5.1 R-3 対策のテスト優先実施もフェーズ 2 内で完結する。

**フェーズ 3（本格的サブエージェント化）**: A-2 + A-3 + A-6 で状態ファイルのインスタンス分離を実装。並列呼び出しに対応。  
工数: M〜L（2〜3 セッション）。`lam-stop-hook.py` のテスト変更が主リスク。

---

## 5. リスクと非推奨事項

### 5.1 重大リスク

| リスク | 内容 | 対策 |
|-------|------|------|
| 状態ファイル競合（R-1） | 複数の full-review インスタンスが同時実行された場合、`lam-loop-state.json` への書き込みが競合する。`atomic_write_json` は使用中だが、読み書き間のレースコンディションは残る | フェーズ 2（最小変更）では直列実行のみを仮定し、並列実行はフェーズ 3 以降で `invocation_id` による分離を実装してから許可する |
| `lam-stop-hook.py` の誤動作（R-2） | Stop hook は `lam-loop-state.json` の単一パスを参照するため、サブエージェントからの full-review 呼び出しが既存のトップレベル実行の Stop hook と干渉する可能性がある | フェーズ 2 では「サブエージェント呼び出し中はトップレベルの full-review を同時実行しない」という運用ルールで回避。フェーズ 3 でハード分離 |
| `run_phase0()` のパス誤り再発（R-3） | 運用知見（W2-P2）として「project_root を渡すこと」が記録されているが、サブエージェント環境では cwd が異なる可能性があり、既存の `python3 -c` コマンドをそのまま流用すると誤動作する | A-6 の実装時に全 `python3 -c` 呼び出しを明示 project_root 渡しに変換。変換後のテストを優先実施 |
| ユーザー対話のサイレント消失（R-4） | `auto_approve=true` にして人間の確認をスキップすると、PM 級 Issue が上位に適切に伝わらないまま処理が進むリスク | PM 級 Issue は必ず構造化報告として上位層に返す設計を先行実装（A-5）し、`auto_approve` のデフォルトは `false` に維持 |

### 5.2 非推奨事項（Zero-Regression 観点）

**やるべきでない改造**:

1. **`lam-stop-hook.py` の動作を根本変更する改造**: Stop hook は既存のテスト（`.claude/hooks/tests/test_stop_hook_autonomous.py` 等）でカバーされており、動作変更はリグレッションリスクが高い。インスタンス分離は「別ファイルを参照するオプション追加」で実現し、既存パスは完全に維持すること。

2. **SKILL.md の既存ステージロジックを大幅書き換えする改造**: Stage 2〜5 の監査・修正・検証ロジックは B-2 full-review 完遂によって確立されたバランスを持つ。rubric 対応を理由にこのロジックを変更すると、既存トップレベル用途で品質が変わる。rubric 照合は「追加レイヤー」として最小侵襲で追加すること。

3. **`review-state/` の構造を一括再設計する改造**: `scale-detection.json`、`static-issues.json` 等の既存状態ファイルのスキーマを変更すると、既存の `scale_detector.py` や `run_pipeline.py` との整合性破壊を招く。状態ファイルスキーマは後方互換フィールド追加のみとし、既存フィールドの削除・型変更はしないこと。

4. **複数行 `python3 -c` の使用**: Git Bash 環境では複数行 `python3 -c` が失敗することが既知（MEMORY.md 運用知見）。新規に追加する `python3 -c` は 1 行以内か、外部スクリプト呼び出しに統一すること。

---

## 6. 参考: Green State 定義との対応

本分析で前提とした Green State 条件（`docs/specs/green-state-definition.md` SSOT）:

- G1: テスト全パス
- G2: lint エラーゼロ
- G3: Critical=0 かつ Warning=0（`code-quality-guideline.md` 準拠）
- G4: 仕様差分ゼロ
- G5: セキュリティチェック通過

改造 (b) で追加する G6（rubric 整合性）は、G1〜G5 が全て通過した後の追加条件として定義する。G1〜G5 は LAM の品質基準であり、G6 はゴール駆動オーケストレーションのタスクゴール条件として位置付ける。

---

## 7. 承認依頼事項

PM に承認を求める判断事項:

1. **改造 (a) の段階的実施方針**: フェーズ 1（受け口のみ）→ フェーズ 2（直列サブエージェント）→ フェーズ 3（並列対応）の 3 段階か、フェーズ 2〜3 を一括実施するか
2. **改造 (b) の G6 実装有無**: Stage 5 に G6 チェックを組み込むか、rubric 照合は grader（B-3 新スキル）側に完全委譲するか
3. **`lam-stop-hook.py` の変更許可**: A-3（Stop hook へのインスタンス識別追加）は既存テストへの影響があるため PM 級変更として別途承認が必要
4. **後方互換性維持（lam-loop-state.json への rubric_path フィールド追加）**: `lam-loop-state.json` への `rubric_path` フィールド追加は後方互換維持を MUST とする。既存フィールドの削除・型変更を行わず、フィールド追加のみで対応すること（§2.2 互換性影響、および §5.2 非推奨事項 3 に基づく）
