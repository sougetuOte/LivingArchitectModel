# 権限等級分類基準

v4.0.0 で導入された変更のリスクレベルに応じた三段階分類。
全てのツール操作・ファイル変更はこの等級に基づいて処理される。

## 権限等級（PG/SE/PM）

> 2026-08-22 に `core-identity.md` から**逐語で移設**（案 A 役割分離 / 移設前は同ファイル §権限等級）。
> **2026-08-29 に導入文 1 文を削除**（ファイル冒頭 3-4 行目と逐語重複していたため）。移設時点の本文はそれ以外不変。

- **PG級**: 自動修正・報告不要（フォーマット、typo、lint 修正等）
- **SE級**: 修正後に報告（テスト追加、内部リファクタリング等）
- **PM級**: 判断を仰ぐ（仕様変更、アーキテクチャ変更等）

迷った場合の判定は **§迷った場合** が正本。第 0 原則の 3 変数（可逆性 / 復旧コスト / 確認のコスト）で判定し、**決まらない場合のみ** SE 級に丸める。ここに条件を複製しない（複製は必ずドリフトする）。

## PG級（自動修正・報告不要）

自明な修正。プロジェクトの振る舞いを変えない変更。

- フォーマット修正（prettier, ruff format 等）
- typo 修正
- lint 違反の自動修正（eslint --fix, ruff check --fix 等）
- import 整理
- テスト失敗の自明な修正（型ミスマッチ等）
- 不要な空白・末尾改行の除去

## SE級（修正後に報告）

技術的な判断を含むが、公開 API や仕様に影響しない変更。

- テストの追加・修正
- 内部リファクタリング（公開 API 不変）
- ドキュメントの細部更新（`docs/` 配下、ただし `docs/specs/` と `docs/adr/` と `docs/internal/` を除く）
- 依存パッケージの minor/patch update
- 内部関数の名前変更（外部インターフェース不変）
- ログ出力の追加・修正
- コメントの追加・修正

## PM級（判断を仰ぐ）

プロジェクトの方向性・仕様・アーキテクチャに影響する変更。人間の承認が必須。

- 仕様変更（`docs/specs/` の変更）
- アーキテクチャ変更（`docs/adr/` の変更）
- `.claude/rules/` の追加・変更
- `.claude/settings*.json` の変更
- 公開 API の変更
- 依存パッケージの major update
- フェーズの巻き戻し
- テストの削除
- 機能の削除

## フェーズとの二軸設計

| | PLANNING | BUILDING | AUDITING |
|--|----------|----------|----------|
| PG | - | 自動修正可 | 自動修正可 |
| SE | - | 修正後報告 | 修正後報告 |
| PM | 承認ゲート | 承認ゲート | 承認ゲート |

## ファイルパスベースの分類（PreToolUse hook 用）

| パスパターン | 等級 | 理由 |
|-------------|------|------|
| **リポジトリ外のパス**（hook 内部表現 `__out_of_root__/`） | **PM** | 射程外への書込（`pre-tool-use.py` が最優先で判定 / **降格キャッシュの対象外**）|
| `docs/specs/*.md` | PM | 仕様変更 |
| `docs/adr/*.md` | PM | アーキテクチャ変更 |
| `docs/internal/*.md` | PM | プロセス SSOT（**Hierarchy of Truth level 2** = `docs/specs/` より上位 / 下記注記）|
| `.claude/rules/*.md`, `.claude/rules/*/*.md` | PM | ルール変更（サブディレクトリ含む） |
| `.claude/settings*.json` | PM | 設定変更 |
| ルート `CLAUDE.md` | PM | プロジェクト憲法（無条件ロードされる唯一の常駐面 / **nested な `CLAUDE.md` は対象外**）|
| `.claude/.session-pm-edit-cache.json` | **PM** | **hook が書く信頼アンカー**（偽造で以後の PM 承認が全て SE へ降格する / 下記注記）|
| `.claude/autonomous-state.json` | **PM** | 同上（`active` 偽装で G1 checker を評価せずに「正常終了」できる）|
| `.claude/gd-session-state.json` | **PM** | 同上（token/time bound の PM エスカレーションを回避できる）|
| `.claude/lam-loop-state.json` | **PM** | 同上（ループ制御を外側から書き換えられる）|
| `docs/` 配下（上記以外） | SE | ドキュメント更新 |
| `src/` 配下 | SE | ソースコード変更（デフォルト） |
| その他 | SE | 安全側に倒す |

> **`CLAUDE.md` 行の入場記録（2026-08-27 / 誕生ゲート取引 #23）**: 本行は実装 `_hook_utils.py` `_PM_PATH_PATTERNS` に 2026-07-26 から存在したが、条文には約 4 週間収載されていなかった（§D 在庫 #5）。**真正な退出 2 件（取引 #21・#22 = `decision-making.md` の MAGI 手続き 2 条項の skill 降格）と引き換えに入場**し、乖離を閉じた。2026-08-26 に無料で閉じる試みは gabriel probe に差し戻されている（`docs/artifacts/clause-gate-ledger.md` §射程内記述）。**これにより L1 は `CLAUDE.md` 編集の事前宣言義務を条文上も負う**。
>
> **`docs/internal/*.md` 行の入場記録（2026-09-04 / `retro-2026-09-04.md` A1 / ユーザー承認済）**: `CLAUDE.md` の Hierarchy of Truth は `docs/internal/00-08` を **level 2**、`docs/specs/` を **level 3** と定めるのに、本表は specs=PM / internal=SE と**逆転させていた**。2026-09-04 に穴を実際に通った —— 247 行の新規 SSOT `docs/internal/08_EXECUTION_DISCIPLINE.md` が**無ゲートで生まれ**、PM ダイアログは参照側（`.claude/rules/` の 12 箇所付替）にのみ発火した。**ゲートが本体ではなく参照に発火していた**。加えて `docs/internal/` は同日 managed 配布物になったため、無ゲートで生まれた条文が利用者へ配られる経路でもあった。**`docs/` 配下の他（`artifacts/` / `private/` / `daily/`）は SE のまま**である —— あれらは記録であって規範ではなく、巻き込むと retro・進捗台帳の毎回書込が PM ダイアログになり「常時鳴る計器は殺される」型に直行する（陰性対照は `test_docs_internal_is_pm_and_other_docs_are_not`）。
>
> **hook が書く信頼アンカー 4 行の入場記録（2026-09-05 / `/full-review` iter0 C-3・C-4 / ユーザー承認済）**: これら 4 ファイルは **hook が書き、hook が読んで判断の根拠にする**。モデルが直接書けると、判断の前提そのものを偽造できる。実測（2026-09-05 / 実際の `_determine_by_path` を呼んで確認）では 4 件とも `('SE', 'default path')` で**無条件に書けた** —— `.session-pm-edit-cache.json` を偽造すれば以後の PM 承認が全て SE へ降格し（判定は `session_id` とパス文字列の一致のみで偽造耐性が無く、`session_id` はトランスクリプトのファイル名として `ls` だけで得られる）、`autonomous-state.json` の `active` を落とせば G1 checker を一度も評価せずにループが「正常終了」する。**射程は Edit / Write 経路のみ**であり、`Bash("cat > ...")` は `file_path` を持たず到達しない —— これは FR-9 / FR-3.4 deny や PLANNING 設定凍結と同じ既知の限界で、本行はそれを変えない。陰性対照は `test_unrelated_state_like_paths_stay_non_pm`（`.claude/logs/permission.log` / `tdd-patterns.log` / `skills/` / `agents/` / `states/` を巻き込んでいないこと）。
>
> **判定は大文字小文字を区別しない（2026-09-05 / 同上 C-2）**: 実行環境は Windows（`CLAUDE.md` §Execution Environment）で NTFS は case-insensitive だが、`normalize_path` の相対パス分岐は FS へ問い合わせない設計のため、`.claude/Rules/security-commands.md`（大文字 R）が**判定は SE・書込先は実在の PM 級ファイル本体**という経路を作っていた。`Claude.md` / `docs/Specs/` でも同様。実装は `_PM_PATH_FLAGS = re.IGNORECASE`。したがって**本表のパスは大文字小文字の任意の組み合わせを含む**と読むこと。検査は `test_pm_gate_case_and_state_files.py`。
>
> **本表が PM 級パス列挙の正本である**（実装は `_hook_utils.py` `_PM_PATH_PATTERNS` / out-of-root のみ `pre-tool-use.py` がローカル保持）。**本ファイル内の他節は本表を参照し、列挙を複製しないこと** —— 複製は必ずドリフトする（2026-08-22 の掃きで実測 / `CLAUDE.md` の欠落が 4 箇所に同時に存在し、約 4 週間発見されなかった）。

## セッションスコープでの PM 級降格（2026-06-29 追加）

同一セッション内で **2 回目以降の同一ファイル編集** は、PM 級を自動的に **SE 級に降格** する。

### 動作仕様

- 対象パス: **§ファイルパスベースの分類 の PM 行すべて**（実装は `_PM_PATH_PATTERNS_FOR_CACHE` = 同一パターン / **out-of-root のみ対象外** = 上表の注記参照）
- 1 回目の Edit/Write: 通常通り **PM 級ダイアログ表示**（ユーザー承認必須）
- ユーザー承認 → ツール正常完了 → PostToolUse hook が当該パスを `.claude/.session-pm-edit-cache.json` に記録
- 同一セッション内の 2 回目以降の Edit: PreToolUse hook がキャッシュ参照し **SE 級に降格**（ダイアログなし / ログのみ）
- セッション境界（`session_id` 変化）でキャッシュ自動失効
- ユーザーが拒否した場合: ツール失敗 → PostToolUse 不発火 → キャッシュ追加されず → 次回も PM 級維持（拒否は記憶されない）

### AUTONOMOUS フェーズの DENY 経路は対象外

FR-9（統治ファイルの自己統治不可侵）/ FR-3.4（spec freeze）の DENY 判定は本緩和の対象外。
AUTONOMOUS フェーズでの統治ファイル / spec 書込は引き続き不可逆 deny として扱う。

### PM 級編集の事前宣言義務（2026-06-29 追加 / 案 B）

> 2026-08-22 に `core-identity.md` から**逐語で移設**（案 A 役割分離 / 上記セッションスコープ降格との併用箇所であるため本節の直下に置く）。

L1（主体）が PM 級ファイル（**§ファイルパスベースの分類 の PM 行すべて**）を
**直接編集する**前に、以下を **1 回だけ宣言** する:

- 編集対象ファイル（具体的なパス）
- 想定編集回数（おおよその目安 / 例: 「2-3 回の Edit」）
- 編集内容の要約（1-2 文）

これは初回の PM 級ダイアログで「何を承認しているか」をユーザーに明示するため。
2 回目以降の同一ファイル編集は `permission-levels.md` のセッションスコープ降格機構により
自動的に SE 級扱いとなる（ダイアログ非表示）ので、再宣言は不要。

#### 不要なケース

- subagent（design-architect / spec-critic 等）経由の編集 → 委譲時のプロンプトが宣言の代わり
- gitignore 済ファイル（`SESSION_STATE.md` 等）→ そもそも PM 級判定対象外

#### 例

> 「これから `docs/specs/<path>/design.md` に R3 修正 7 件を入れます (Edit 3-5 回想定)。承認お願いします」

### 実装

- 判定: `.claude/hooks/pre-tool-use.py`（`_is_pm_already_approved` 関数）
- 記録: `.claude/hooks/post-tool-use.py`（`_handle_pm_edit_cache` 関数）
- キャッシュ: `.claude/.session-pm-edit-cache.json`（gitignore 済 / ローカル限定）

## 迷った場合

まず**第 0 原則の 3 変数**（可逆性 / 復旧コスト / 確認のコスト）で判定する。
定義は `.claude/rules/core-identity.md` §第 0 原則 が**正本**。

3 変数の適用:
- 可逆かつ復旧コスト低 → PG-SE 級で進む (確認のコストが高すぎるため)
- 不可逆または復旧コスト高 → PM 級に倒す
- 3 変数で決まらない場合のみ **SE 級に丸める**（安全側に倒す）

判断に迷う典型例:
- 「テストの大幅な書き換え」→ SE級（公開 API は変わらない / 可逆・復旧コスト低）
- 「README の構成変更」→ SE級（仕様書ではない）
- 「.claude/commands/ の変更」→ SE級（ルールではなくコマンド）
- 「package.json の scripts 変更」→ SE級（ビルド設定）
- 「.gitignore の変更」→ SE級

## PM 級パスの事前計算原則 (2026-07-07 追加 / L3 導入)

上記「ファイルパスベースの分類」で PM 級として列挙されたパス (**同表が正本** / ここに複製しない) は **ユーザーが事前計算した第 0 原則の出力** (= 不可逆・高 stakes と事前宣言済み) である。

**実行時に第 0 原則の 3 変数で再導出して PM 級を PG/SE に降格することは禁止する**。理由: PM 級パスは事前に「不可逆」判定済であり、可逆性 (git 巻き戻し可否) を根拠に降格するとメタ規範の書き換えとなる。git で巻き戻せる編集でも PM 級パスなら**承認ゲートを通す** (セッションスコープ降格機構は例外 = 同一セッション内 2 回目以降の同一ファイル編集のみ)。

第 0 原則が実行時に生きるのは本ファイルの「迷った場合」節 (= 未割当領域) のみ。

## 参照

- `docs/specs/v4.0.0-immune-system-requirements.md` Section 5.1 (権限等級の原定義)
- `docs/internal/07_SECURITY_AND_AUTOMATION.md` Section 5 (Hooks-Based Permission System)
- `docs/internal/02_DEVELOPMENT_FLOW.md` (フェーズ別の権限適用)
