# gitleaks 統合 要件仕様書

**バージョン**: 1.0
**作成日**: 2026-03-17
**ステータス**: approved
**関連 Issue**: A（SECRET_PATTERN JSON/YAML 対応）、D（.md/.txt スキャン対象追加）
**関連仕様**: `scalable-code-review-spec.md` FR-7e（D-0: シークレットスキャン Phase 0 統合）

---

## 1. 目的

gitleaks を LAM のシークレットスキャン基盤として統合し、
言語・ファイル形式を問わない包括的なシークレット検出を実現する。

## 2. 背景

### 2.1 現状の問題

| 問題 | 詳細 |
|------|------|
| 検出範囲の限界 | bandit B105/B106 は Python ファイルのみ対象 |
| 形式の未対応 | `password: "secret"`（YAML/JSON コロン形式）を検出できない |
| スキャン対象外 | `.md`, `.txt`, `.yaml`, `.json` 等がスキャン対象外 |
| 認知の網の外 | 推奨ツールとして文書化しても読まれない。シークレット漏洩は「すり抜けたことに気づかない」性質を持つ |

### 2.2 なぜパイプライン統合なのか

シークレット漏洩は人間の認知系にとって特殊な性質を持つ:

- **すり抜けやすい**: コードレビューでもシークレットの混入は見落としやすい
- **気づきにくい**: すり抜けた事実にも気づかない（漏洩の発覚は外部からの通知が多い）
- **推奨では防げない**: 「gitleaks を使ってください」と文書化しても読まれない

これは通常なら文書推奨で済ませる領域だが、上記の性質から**正規系を崩してでもパイプラインに組み込むべき**と判断した。受動的な防御（文書推奨）ではなく、能動的な検出（自動実行）にすることで、人間の認知限界を技術で補完する。

### 2.3 なぜ自前パターンではなく専用ツールか

- gitleaks は 800+ のルール（正規表現 + エントロピー分析）を持ち、継続的に更新される
- 自前パターンの保守コストと偽陽性/偽陰性のトレードオフを回避できる
- 業界標準ツールであり、検出精度の実績がある

## 3. 要件

### FR-1: full-review パイプラインへの統合（detect モード）

full-review（AUDITING フェーズ）の静的解析ステップに gitleaks を統合する。

- `gitleaks detect` でリポジトリ全体をスキャンする
- 検出結果を既存の Issue 体系（`base.py` の `Issue` dataclass）に変換する
- 検出された Issue は **Critical** として分類する（シークレット漏洩はデータ損失リスク）
- Green State を阻害する（Critical = 0 の条件に含まれる）

### FR-2: コミット前の差分スキャン（protect モード）

`/ship` コマンドまたは手動コミット前に、ステージング済みの変更に対して gitleaks を実行する。

- `gitleaks protect --staged` で staged changes のみスキャンする
- 検出があった場合はコミットを阻止し、検出内容を報告する
- ユーザーが「承知の上で続行」と明示した場合のみ、スキャン結果を無視してコミットできる

### FR-3: クロスプラットフォーム動作

以下の環境で動作すること:

| 環境 | MUST/SHOULD |
|------|-------------|
| Linux Bash | MUST |
| Windows Git Bash | MUST |
| macOS | SHOULD |

gitleaks は Go 製の単一バイナリであり、上記全環境で動作実績がある。

### FR-4: ツール未インストール時の動作

gitleaks がインストールされていない場合の動作:

- **full-review 時**: **G5 FAIL**（Green State 未達）。インストールガイドを表示し、gitleaks の導入を求める。他の静的解析は続行するが、gitleaks がインストールされるまで Green State は達成できない（何度再実行しても G5 が FAIL のまま）
- **コミット前スキャン時（/ship）**: WARNING を出力し、コミットは許可する

**理由**:
- full-review は品質の門番であり、シークレットスキャン未実施での Green State 達成を許容しない
- /ship は日常作業であり、FAIL にすると迂回される（`git commit` を直接叩く等）リスクがある。WARNING で意識に留める方が実効性が高い

### FR-4a: インストールガイドの表示

gitleaks 未検出時に以下の情報を含むメッセージを表示する:

1. **gitleaks とは何か**: シークレット自動検出の業界標準ツールであること
2. **なぜ必要か**: シークレット漏洩は認知の網をすり抜けやすく、パイプラインでの自動検出が必要であること
3. **インストール方法**: 公式リポジトリの URL と、主要環境ごとのインストールコマンド（Homebrew, Scoop, Go install, バイナリ直接ダウンロード）

### FR-4b: 明示的オプトアウト

ユーザーが gitleaks を不要と判断した場合、`review-config.json` に `"gitleaks_enabled": false` を
設定することで gitleaks スキャンを無効化できる。

- **full-review 時**: gitleaks スキャンをスキップし、G5 は PASS 扱い
- **コミット前スキャン時**: gitleaks スキャンをスキップ
- INFO ログで「gitleaks は明示的に無効化されています」と記録する（沈黙しない）

**理由**: 「知らずにすり抜ける」と「知った上で不要と判断する」は異なる。後者を尊重する。

### FR-5: 設定ファイル

プロジェクトルートに `.gitleaks.toml` を配置し、以下を設定可能とする:

- 除外パス（テストフィクスチャ等）
- 除外ルール（特定の正規表現パターン）
- カスタムルールの追加

LAM のデフォルト設定として、以下を除外する:
- `.claude/hooks/analyzers/tests/fixtures/` 配下（テストフィクスチャにハードコードパスワードが意図的に含まれる）

### FR-6: 既存 FR-7e との統合

`scalable-code-review-spec.md` の FR-7e（D-0: シークレットスキャン Phase 0 統合）を
gitleaks に置き換える:

- `lam-stop-hook.py` の `_SECRET_PATTERN` / `_SAFE_PATTERN` は削除方針を維持
- bandit B105/B106 は Python 固有の検出として残留（gitleaks と補完関係）
- gitleaks が全ファイル形式の包括スキャンを担当

## 4. 非機能要件

### NFR-1: 実行時間

| 対象 | 目安 |
|------|------|
| `gitleaks protect --staged`（差分） | 5秒以内 |
| `gitleaks detect`（全体、~30K行） | 30秒以内 |

### NFR-2: 外部依存

gitleaks バイナリのみ。追加の Python パッケージ依存は不要。
gitleaks のインストールはユーザー責任とし、LAM は自動インストールしない。

### NFR-3: 出力形式

gitleaks は JSON 出力（`--report-format json`）を使用し、
Python スクリプトで Issue dataclass に変換する。

## 5. スコープ外

- gitleaks の自動インストール機構
- CI/CD パイプラインへの組み込み（ユーザーのプロジェクト側の責務）
- git history スキャン（`gitleaks detect` はデフォルトで HEAD のみ）
- エントロピー分析のカスタムチューニング

## 6. 成功基準

| # | 基準 | 検証方法 |
|---|------|---------|
| S-1 | `password: "secret"` 形式が検出される | テストフィクスチャで検証 |
| S-2 | `.md` ファイル内のシークレットが検出される | テストフィクスチャで検証 |
| S-3 | full-review で gitleaks 結果が Issue に含まれる | full-review 実行で確認 |
| S-4 | コミット前スキャンでシークレットが阻止される | `/ship` 実行で確認 |
| S-5 | gitleaks 未インストール時に full-review で G5 FAIL + インストールガイドが表示される | gitleaks なし環境で確認 |
| S-5a | gitleaks 未インストール時に /ship で WARNING + コミット許可される | gitleaks なし環境で確認 |
| S-6 | Linux Bash で動作する | 開発環境で検証 |
| S-7 | .gitleaks.toml の除外設定が機能する | テストフィクスチャ除外で検証 |

## 7. 参照

- gitleaks 公式: https://github.com/gitleaks/gitleaks
- 延期 Issue A: `project_next_tasks.md`（SECRET_PATTERN JSON/YAML 対応）
- 延期 Issue D: `project_next_tasks.md`（.md/.txt スキャン対象追加）
- 既存仕様: `docs/specs/scalable-code-review-spec.md` FR-7e
- 品質基準: `.claude/rules/code-quality-guideline.md`（Critical 分類）
