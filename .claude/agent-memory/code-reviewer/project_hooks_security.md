---
name: hooks security findings
description: .claude/hooks/ セキュリティ監査結果と要注意箇所（2026-06-10 イテレーション2更新）
metadata:
  type: project
---

2026-06-10 イテレーション2 SEC横断監査で更新（ゼロベース監査、全対象ファイル再読込）。

**Why:** フックスクリプトは Claude Code の権限制御レイヤーであり、迂回・誤動作は直接的なセキュリティリスクになる。

**How to apply:** hooks/ 関連コードをレビューする際は以下の点を優先確認する。

## 要注意箇所（優先度順）

### 残存オープン（2026-06-10 イテレーション2 確認）

1. [Low/SE] `analyzers/gitleaks_scanner.py:241` — `_parse_gitleaks_json` で `data` が
   list でない場合（dict/None）に `for finding in data:` が AttributeError を送出して
   `run_phase0` までクラッシュ伝播する。gitleaks v8 は通常 `[]` を返すが、異常終了時に
   JSON object を返すバージョンや将来の形式変更で露出する。
   修正: `if not isinstance(data, list): return []` を json.loads 直後に追加。
   （iter1 で Critical と報告されたが、gitleaks v8 の通常動作では非発生。Low に降格）

2. [Low/SE] `pre-compact.py:46` — `write_pre_compact_flag` が `path.write_text()` で
   非アトミック書込み。中断時に空/部分書込みになる。
   lam-stop-hook の fromisoformat 失敗時は mtime フォールバックがあるため
   セキュリティ影響はなく Low。`_atomic_write_text()` に置き換えが望ましい。

### 解消済み（2026-06-10 イテレーション1→2 で修正確認）

- `check_g1_test.py run_check`: `env=build_allowlisted_env()` 適用済み（iter1 item 3）
- `gitleaks_scanner.py _run_gitleaks`: `env=build_allowlisted_env()` 適用済み（iter1 item 4）
- `python/javascript/rust_analyzer.py`: 全 subprocess に `build_allowlisted_env()` 適用済み（iter1 item 5）
- `analyzers/base.py auto_discover`: `resolve().parent != resolved_dir` チェックで symlink 越境ロードをブロック済み（iter1 item 1 相当）
- `normalize_path`: W-15 symlink resolve + W-16 `..` 字句畳み込み済み
- `lam-stop-hook.py _run_g1_checker`: `build_allowlisted_env()` 適用済み

### iter2 新規確認（指摘なし相当）

- `_PG_BLACKLISTED_ARGS` `\$` パターン: Python 3 `\s` は Unicode 空白を含むためマッチ漏れなし
- `--config` が文字列末尾で終わる場合のバイパス: ruff が「値なし」でエラー終了するため実害なし（理論上のみ）
- ET.parse XXE: Python の expat が外部エンティティ参照を ParseError で拒否 — 安全
- ET.parse Billion Laughs: expat 組込み増幅係数制限が 6 レベル以上で発火 — 安全
- gitleaks tempfile TOCTOU: gitleaks が上書きするため読取側の整合性は維持される — 影響なし
- tdd-patterns.log 改行注入: tab 置換済み + 不正行は splitlines 後に `len(fields) < 2` でスキップ

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
