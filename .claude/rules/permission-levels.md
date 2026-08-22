# 権限等級分類基準

v4.0.0 で導入された変更のリスクレベルに応じた三段階分類。
全てのツール操作・ファイル変更はこの等級に基づいて処理される。

## 権限等級（PG/SE/PM）

> 2026-08-22 に `core-identity.md` から**逐語で移設**（案 A 役割分離 / 移設前は同ファイル §権限等級）。

v4.0.0 で導入された変更のリスクレベルに応じた三段階分類:

- **PG級**: 自動修正・報告不要（フォーマット、typo、lint 修正等）
- **SE級**: 修正後に報告（テスト追加、内部リファクタリング等）
- **PM級**: 判断を仰ぐ（仕様変更、アーキテクチャ変更等）

迷った場合は SE級に丸める（安全側に倒す）。

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
- ドキュメントの細部更新（`docs/` 配下、ただし `docs/specs/` と `docs/adr/` を除く）
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
| `docs/specs/*.md` | PM | 仕様変更 |
| `docs/adr/*.md` | PM | アーキテクチャ変更 |
| `.claude/rules/*.md`, `.claude/rules/*/*.md` | PM | ルール変更（サブディレクトリ含む） |
| `.claude/settings*.json` | PM | 設定変更 |
| `docs/` 配下（上記以外） | SE | ドキュメント更新 |
| `src/` 配下 | SE | ソースコード変更（デフォルト） |
| その他 | SE | 安全側に倒す |

## セッションスコープでの PM 級降格（2026-06-29 追加）

同一セッション内で **2 回目以降の同一ファイル編集** は、PM 級を自動的に **SE 級に降格** する。

### 動作仕様

- 対象パス: `docs/specs/*.md` / `docs/adr/*.md` / `.claude/rules/*.md` / `.claude/settings*.json`
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

L1（主体）が PM 級ファイル（`docs/specs/` / `docs/adr/` / `.claude/rules/` / `.claude/settings*.json`）を
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

上記「ファイルパスベースの分類」で PM 級として列挙されたパス (`docs/specs/*.md` / `docs/adr/*.md` / `.claude/rules/*.md` / `.claude/settings*.json`) は **ユーザーが事前計算した第 0 原則の出力** (= 不可逆・高 stakes と事前宣言済み) である。

**実行時に第 0 原則の 3 変数で再導出して PM 級を PG/SE に降格することは禁止する**。理由: PM 級パスは事前に「不可逆」判定済であり、可逆性 (git 巻き戻し可否) を根拠に降格するとメタ規範の書き換えとなる。git で巻き戻せる編集でも PM 級パスなら**承認ゲートを通す** (セッションスコープ降格機構は例外 = 同一セッション内 2 回目以降の同一ファイル編集のみ)。

第 0 原則が実行時に生きるのは本ファイルの「迷った場合」節 (= 未割当領域) のみ。

## 参照

- `docs/specs/v4.0.0-immune-system-requirements.md` Section 5.1 (権限等級の原定義)
- `docs/internal/07_SECURITY_AND_AUTOMATION.md` Section 5 (Hooks-Based Permission System)
- `docs/internal/02_DEVELOPMENT_FLOW.md` (フェーズ別の権限適用)
