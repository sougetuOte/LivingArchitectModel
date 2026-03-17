# gitleaks 統合 設計書

**バージョン**: 1.0
**作成日**: 2026-03-17
**ステータス**: approved
**対応仕様**: `docs/specs/gitleaks-integration-spec.md`

---

## 1. Problem Statement

現在のシークレット検出は bandit B105/B106（Python のみ）に依存しており、
YAML/JSON 形式のシークレットや `.md`/`.txt` 内のシークレットを検出できない。

シークレット漏洩は「すり抜けたことに気づかない」性質を持ち、推奨ツールとして
文書化しても読まれない。正規系を崩してでもパイプラインに組み込む必要がある。

## 2. Non-Goals（非スコープ）

- gitleaks の自動インストール機構
- `LanguageAnalyzer` プラグインとしての実装（gitleaks は言語非依存のため不適合）
- git history 全体のスキャン
- CI/CD パイプラインへの組み込み

## 3. Alternatives Considered

| 案 | 採否 | 理由 |
|----|------|------|
| A: gitleaks をパイプラインに統合 | **採用** | 単一バイナリ、クロスプラットフォーム、800+ ルール |
| B: 自前パターン拡張 | 却下 | 保守コスト大、エントロピー分析不可、偽陽性リスク |
| C: detect-secrets (Python) | 却下 | Python 依存、Git Bash での動作にPython環境が必要 |
| D: truffleHog | 候補 | gitleaks と同等だが、コミュニティ規模で gitleaks を優先 |

## 4. Success Criteria

- 仕様書 Section 6（S-1〜S-7）の全基準を満たすこと
- 既存の 435+ テストが壊れないこと

## 5. アーキテクチャ設計

### 5.1 統合ポイント（2箇所）

```
統合ポイント 1: /full-review Stage 1（detect モード）
┌──────────────────────────────────────────────┐
│ Stage 1: 静的分析 + 依存グラフ構築            │
│                                               │
│  Step 1: 静的解析（既存: ruff, bandit, etc.） │
│  Step 1.5: gitleaks detect ← NEW              │
│  Step 2: 静的解析結果の Stage 2 接続           │
│  Step 3: 依存グラフ構築                       │
└──────────────────────────────────────────────┘

統合ポイント 2: /ship Phase 1（protect モード）
┌──────────────────────────────────────────────┐
│ Phase 1: 棚卸し                               │
│                                               │
│  Step 1: git status + git diff（既存）        │
│  Step 1.5: gitleaks protect --staged ← NEW    │
│  Step 2: 秘密情報パターン検出（既存）         │
│  Step 3: 変更ファイル一覧表示                 │
└──────────────────────────────────────────────┘
```

### 5.2 gitleaks ラッパーモジュール

gitleaks バイナリの呼び出しと結果変換を担当する Python モジュールを新設する。
`LanguageAnalyzer` プラグインではなく、独立したユーティリティとして配置する。

**配置先**: `.claude/hooks/analyzers/gitleaks_scanner.py`

**理由**: gitleaks は言語非依存であり、`LanguageAnalyzer` の `language_name` / `detect()` /
`run_lint()` / `run_security()` のインターフェースに合致しない。
既存の analyzers ディレクトリに配置するのは、静的解析ツール群との一貫性のため。

```
gitleaks_scanner.py
├── is_available() -> bool
│   gitleaks バイナリが PATH に存在するか確認
│
├── run_detect(project_root, config_path=None, *, enabled=True) -> list[Issue]
│   gitleaks detect でリポジトリ全体をスキャン
│   未インストール時: rule_id="gitleaks:not-installed" の Critical Issue
│   タイムアウト時: rule_id="gitleaks:scan-timeout" の Critical Issue
│   実行失敗時: rule_id="gitleaks:scan-failed" の Critical Issue
│   enabled=False: 空リスト + INFO ログ（明示的オプトアウト）
│
├── run_protect_staged(project_root=None, config_path=None, *, enabled=True) -> list[Issue]
│   gitleaks protect --staged で staged changes をスキャン
│   未インストール・無効化時: 空リスト
│   project_root 指定時: .gitleaks.toml を自動検出
│
├── get_install_guide() -> str
│   インストールガイドメッセージを返す（FR-4a）
│
├── _resolve_config(project_root, config_path) -> Path | None
│   .gitleaks.toml の自動検出（共通処理）
│
├── _run_gitleaks(cmd, timeout) -> list[Issue]
│   gitleaks コマンド実行 + JSON パース + 例外処理（共通ヘルパー）
│
└── _parse_gitleaks_json(json_path) -> list[Issue]
    gitleaks JSON → Issue 変換（Match/Secret は格納しない）
```

### 5.3 Issue 変換マッピング

gitleaks の JSON 出力フィールドを `Issue` dataclass にマッピングする。

| gitleaks フィールド | Issue フィールド | 変換 |
|:-------------------|:----------------|:-----|
| `File` | `file` | そのまま |
| `StartLine` | `line` | そのまま |
| `RuleID` | `rule_id` | `"gitleaks:" + RuleID` |
| `Description` | `message` | そのまま |
| — | `severity` | 固定 `"critical"` |
| — | `category` | 固定 `"security"` |
| — | `tool` | 固定 `"gitleaks"` |
| `Match` | — | **マッピングしない**（シークレット値の露出防止。固定文字列 `_SUGGESTION` を使用） |

### 5.4 full-review Stage 1 への統合

`run_phase0()` の末尾で gitleaks を呼び出す。

```python
# run_pipeline.py の run_phase0() に追加（概念）
from .gitleaks_scanner import run_detect

# gitleaks は内部で is_available() を判定し、
# 未インストール時は not-installed Issue、実行失敗時は scan-failed Issue を返す。
# enabled=False（明示的オプトアウト）時は空リストを返す。
issues.extend(run_detect(project_root, enabled=config.gitleaks_enabled))
```

**重要**: gitleaks 未インストール時の動作は full-review と /ship で異なる（FR-4）:
- **full-review**: G5 FAIL（Green State 未達）+ インストールガイド表示。静的解析は続行するが Green State は達成できない
- **/ship**: WARNING + スキップ。コミットは許可する（日常作業の過剰な摩擦を避ける）
- **明示的オプトアウト**（`review-config.json` で `gitleaks_enabled: false`）: スキップ + INFO ログ。G5 は PASS

### 5.4a インストールガイドメッセージ（FR-4a）

gitleaks 未検出時に `gitleaks_scanner.py` が生成するメッセージ:

```
⚠️ gitleaks が未インストールのため、Green State G5（セキュリティ）が未達です。

【影響】
  gitleaks がインストールされるまで Green State を達成できません。
  /full-review はシークレットスキャン未実施を Critical Issue として扱い、
  何度再実行しても G5 が FAIL のままになります。
  インストール後に再実行すれば解消されます。

【gitleaks とは】
  シークレット（API キー、パスワード等）がコードに紛れ込んでいないかを
  自動検出する業界標準ツールです。Go 製の単一バイナリで、
  Linux / macOS / Windows（Git Bash）で動作します。

【インストール方法】
  公式: https://github.com/gitleaks/gitleaks#installing

  # Linux / macOS（Homebrew）
  brew install gitleaks

  # Windows（Scoop）
  scoop install gitleaks

  # Go がある環境
  go install github.com/gitleaks/gitleaks/v8@latest

【なぜ必要か】
  シークレット漏洩は「すり抜けたことに気づかない」性質を持ちます。
  推奨ツールとして文書化するだけでは防げないため、
  LAM はパイプラインに組み込んで自動検出します。
```

このメッセージは `gitleaks_scanner.py` の `get_install_guide()` 関数で返す。
full-review では Issue（Critical, tool="gitleaks", rule_id="gitleaks:not-installed"）として
レポートに含め、/ship では WARNING テキストとして表示する。

### 5.5 /ship Phase 1 への統合

`/ship` コマンドの Phase 1 に gitleaks protect を追加する。

```
Phase 1 フロー（変更後）:
1. git status + git diff（既存）
2. gitleaks protect --staged（NEW）
   ├── 検出なし → Step 3 へ
   └── 検出あり → 警告表示 + ユーザー判断
       ├── 「承知の上で続行」→ Step 3 へ
       └── それ以外 → コミット中止
3. 秘密情報パターン検出（既存）
4. 変更ファイル一覧表示
```

### 5.6 full-review Stage 5 G5 の更新

現在の G5 セキュリティチェックに gitleaks 結果を追加する。

| チェック項目 | ツール | 変更 |
|:---|:---|:---|
| 依存脆弱性 | `pip audit` / `npm audit` | 変更なし |
| シークレット漏洩 | ~~`grep` パターン~~ **gitleaks** | **置換** |
| 危険パターン | OWASP Top 10 | 変更なし |

### 5.7 .gitleaks.toml（デフォルト設定）

```toml
[extend]
# gitleaks デフォルトルールを継承

[allowlist]
  paths = [
    '''.claude/hooks/analyzers/tests/fixtures/''',
  ]
```

テストフィクスチャにはハードコードパスワードが意図的に含まれるため除外する。
`docs/memos/` 等は除外しない（検討メモに API キーを貼り付けるケースこそ
「認知の網の外」であり、スキャン対象とすべきため）。

## 6. テスト方針

### 6.1 ユニットテスト

| テスト | 内容 |
|--------|------|
| `test_is_available` | PATH に gitleaks がある/ない場合の判定 |
| `test_parse_gitleaks_json` | gitleaks JSON → Issue 変換の正確性 |
| `test_run_detect_not_installed` | 未インストール時に not-installed Issue が返る |
| `test_get_install_guide` | インストールガイドメッセージにURL・コマンドが含まれる |
| `test_run_detect_no_findings` | 検出なし時に空リスト |
| `test_run_detect_with_findings` | 検出あり時に Issue リストが返る |
| `test_run_protect_staged` | staged 差分スキャンの動作 |
| `test_issue_severity_is_critical` | 全 Issue が Critical であること |
| `test_gitleaks_toml_allowlist` | 除外パスが機能すること |

### 6.2 統合テスト

| テスト | 内容 |
|--------|------|
| `test_run_phase0_includes_gitleaks` | run_phase0() に gitleaks 結果が含まれる |
| `test_run_phase0_without_gitleaks` | gitleaks なしでも run_phase0() が動作する |

### 6.3 テスト時の gitleaks モック

ユニットテストでは gitleaks バイナリを呼び出さず、
`subprocess.run` をモックして JSON 出力を返す。
統合テストも同様にモックを使用する（gitleaks の CI インストールは不要）。

## 7. 影響範囲

| ファイル | 変更種別 | 内容 |
|---------|---------|------|
| `.claude/hooks/analyzers/gitleaks_scanner.py` | **新規** | gitleaks ラッパーモジュール |
| `.claude/hooks/analyzers/run_pipeline.py` | 修正 | run_phase0() に gitleaks 呼び出し追加 |
| `.claude/commands/ship.md` | 修正 | Phase 1 に gitleaks protect 追加 |
| `.claude/commands/full-review.md` | 修正 | Stage 1 Step 1.5 追加、G5 更新 |
| `.gitleaks.toml` | **新規** | デフォルト設定 |
| `tests/test_gitleaks_scanner.py` | **新規** | ユニットテスト |
| `docs/specs/gitleaks-integration-spec.md` | 既存 | 本設計の対応仕様 |

## 8. 参照

- gitleaks JSON output format: `[{"RuleID": "...", "File": "...", "StartLine": N, ...}]`
- 既存 Issue dataclass: `.claude/hooks/analyzers/base.py`
- 既存パイプライン: `.claude/hooks/analyzers/run_pipeline.py`
- full-review: `.claude/commands/full-review.md`
- /ship: `.claude/commands/ship.md`
