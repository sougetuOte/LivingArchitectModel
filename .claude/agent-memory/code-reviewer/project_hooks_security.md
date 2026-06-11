---
name: hooks security findings
description: .claude/hooks/ セキュリティ監査結果と要注意箇所（2026-06-10 イテレーション2更新）
metadata:
  type: project
---

2026-06-11 イテレーション6 SEC ゼロベース再スキャンで更新（全対象ファイル再読込）。

**Why:** フックスクリプトは Claude Code の権限制御レイヤーであり、迂回・誤動作は直接的なセキュリティリスクになる。

**How to apply:** hooks/ 関連コードをレビューする際は以下の点を優先確認する。

## 要注意箇所（優先度順）

### 残存オープン（2026-06-11 イテレーション6 最終確認）

なし。iter6 全域ゼロベース再スキャン（全12本番ファイル再読込）で新規 Issue なし。Issues: 0。

追加確認事項（iter6）:
- `python/javascript/rust_analyzer.py` の全 subprocess: `shell=` 未指定（Python デフォルト False）だが、リスト引数渡しのため実害なし
- `run_command()` — 削除済み（grep で0件再確認）
- `eval`/`exec`/`pickle`/`yaml.load` — 本番コードに不使用（grep 再確認）
- ハードコード認証情報 — 全ファイル再スキャンで不在確認

### 解消済み（iter1〜4 累積確認）

- `check_g1_test.py run_check`: `env=build_allowlisted_env()` 適用済み（iter1 item 3）
- `gitleaks_scanner.py _run_gitleaks`: `env=build_allowlisted_env()` 適用済み（iter1 item 4）
- `python/javascript/rust_analyzer.py`: 全 subprocess に `build_allowlisted_env()` 適用済み（iter1 item 5）
- `analyzers/base.py auto_discover`: `resolve().parent != resolved_dir` チェックで symlink 越境ロードをブロック済み（iter1 item 1 相当）
- `normalize_path`: W-15 symlink resolve + W-16 `..` 字句畳み込み済み
- `lam-stop-hook.py _run_g1_checker`: `build_allowlisted_env()` 適用済み

### iter2〜4 新規確認（指摘なし相当）

- `_PG_BLACKLISTED_ARGS` `\$` パターン: Python 3 `\s` は Unicode 空白を含むためマッチ漏れなし
- `--config` が文字列末尾で終わる場合のバイパス: ruff が「値なし」でエラー終了するため実害なし（理論上のみ）
- ET.parse XXE: Python の expat が外部エンティティ参照を ParseError で拒否 — 安全
- ET.parse Billion Laughs: expat 組込み増幅係数制限が 6 レベル以上で発火 — 安全
- gitleaks tempfile TOCTOU: gitleaks が上書きするため読取側の整合性は維持される — 影響なし
- tdd-patterns.log 改行注入: tab 置換済み + 不正行は splitlines 後に `len(fields) < 2` でスキップ
- `run_command()` `env` 未指定: iter5 で完全削除を grep 確認（0件）。解消済み
- `eval`/`exec`/`pickle`/`yaml.load`: iter4 全域再確認で不使用を確認
- 全 subprocess `shell=False`: iter4 全域再確認済み
- ハードコード認証情報: iter4 全域再確認で不在を確認

## 良好な点（参照用）

- 全 subprocess で `shell=False` 確認済み（iter2 再確認）
- 全 analyzer subprocess で `build_allowlisted_env()` 適用済み（iter2 確認）
- `atomic_write_json` で JSON ファイルの競合状態を防止
- `shutil.which()` でコマンドパス解決（PATH インジェクション対策）
- `eval`/`exec`/`pickle`/`yaml.load` の不使用を全域確認済み（iter2 確認）
- gitleaks の Match/Secret フィールドを Issue に格納しない設計（シークレット値の永続化防止）
- FR-9/FR-3.4 の二重防御（pre-tool-use.py 層2 + settings.autonomous.json 層1）
- `_sanitize_target()` による Cc/Cf 制御文字除去（Trojan Source 型ログ偽装防止）
- `normalize_path()` の W-15（symlink 展開）+ W-16（`..` 字句畳み込み）対策
- ET.parse XXE/Billion Laughs: Python expat の組込み保護で安全（iter2 実行検証済み）
- `auto_discover` の `resolve().parent != resolved_dir` symlink バウンダリチェック確認済み
- `except Exception` の多用はフック障害で Claude をブロックしない設計方針に基づく意図的なもの
