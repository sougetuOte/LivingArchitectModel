# 監査レポート S2c: 言語別アナライザ + gitleaks
対象: `.claude/hooks/analyzers/python_analyzer.py` / `javascript_analyzer.py` / `rust_analyzer.py` / `gitleaks_scanner.py`
日付: 2026-06-01 / Pass 1

---

## サマリー
Critical: 2 / Warning: 5 / Info: 4 ／ 評価: **Yellow**

Critical が 2 件あるため Green State 未達。
主要問題は (1) `gitleaks_scanner.py` の `_run_gitleaks` における例外メッセージへの例外値の直接埋め込み（潜在的シークレット漏洩）、および (2) `rust_analyzer.py` の `run_security` での stdout 空判定ロジックの誤り。

---

## Critical

### [Critical-1] gitleaks_scanner.py:213 — 例外値を Issue.message に埋め込む（シークレット漏洩リスク）

```
except Exception as exc:
    ...
    message=f"gitleaks の実行に失敗しました: {exc}",
```

根拠:
`OSError`, `FileNotFoundError`, その他 OS 例外の `str(exc)` には、場合によってパス・環境変数展開結果・
シェルエラーメッセージが含まれることがある。
gitleaks はコマンドライン引数 (`--source`, `--config`) にパスを渡すため、OSError が発生した場合に
`exc` 文字列がそのままログ・Issue.message に永続化される。
これは設計書冒頭の「Match/Secret フィールドを Issue に格納しない」精神と方向性が同じ問題
（実行失敗の例外情報の不用意な露出）。
より大きなリスクは、`_run_gitleaks` が `cmd` リストを受け取って実行するが、`cmd` には既に
プロジェクトパス・設定ファイルパスが含まれており、例外発生時の `exc` にこれらが漏れた場合、
Issue.suggestion ではなく Issue.message として下流カードに掲載される。
さらに、Issue.message は `gitleaks の実行に失敗しました: {exc}` という形で `exc` を **f-string で展開** しており、
`exc.__str__()` が長大なトレースバックを含むサブクラスの場合にもそのまま格納される。

修正案:
```python
except Exception as exc:
    logger.error("gitleaks failed: %s: %s", type(exc).__name__, exc)
    return [
        Issue(
            ...
            message="gitleaks の実行に失敗しました。詳細はログを確認してください。",
            ...
        )
    ]
```
例外詳細はロガーにのみ渡し、Issue.message からは除去する。
等級: **SE**

---

### [Critical-2] rust_analyzer.py:145 — `cargo audit` 未インストール判定が不完全

```python
if not result.stdout.strip() and result.returncode != 0:
    logger.warning("cargo audit not available. ...")
    return []
```

根拠:
`cargo audit` がインストールされていない場合の実際の挙動:
- cargo がサブコマンドを認識しない場合、stderr に `error: no such subcommand: audit` と出力し、returncode=101 を返す
- stdout は空になる → この条件は正しく動作する

しかし条件の問題は **論理の逆** にある:
「stdout が空 **かつ** returncode != 0」の場合のみ未インストール扱い。
一方、脆弱性ゼロ正常終了 (returncode=0, stdout に `{"vulnerabilities": {"found": false, ...}}`) の場合でも
stdout が空でない（正常パース可能）ため問題なし。

本当の問題: **returncode=0 かつ stdout 空** のケースが未考慮。
`cargo audit` は脆弱性なしでも空の JSON を出力することがあるが（`{}`）、
空文字列（stdout.strip() == ""）かつ returncode=0 の場合は現在 `json.loads("")` が
`JSONDecodeError` を発生させ、**Silent Failure**（空リストを返し、ログも出ない）になる。

コードの実際のフロー:
1. `not result.stdout.strip()` が True → かつ `result.returncode != 0` → 未インストールメッセージ、return
2. `not result.stdout.strip()` が True → かつ `result.returncode == 0` → 下の `json.loads("")` に到達 → `JSONDecodeError` → 空リスト返却（ログなし）

この「stdout 空 + returncode=0」のケースは正常終了の特殊ケースとして扱い、ログを出力すべき。

修正案:
```python
stdout = result.stdout.strip()
if not stdout:
    if result.returncode != 0:
        logger.warning("cargo audit not available. Install with: cargo install cargo-audit")
    else:
        logger.debug("cargo audit returned empty output with returncode=0")
    return []
```
等級: **SE**

---

## Warning

### [Warning-1] gitleaks_scanner.py:176 — tempfile リークリスク（例外 + tempfile 競合）

```python
with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
    report_path = Path(tmp.name)
cmd.extend(["--report-path", str(report_path)])
```

根拠:
`NamedTemporaryFile(delete=False)` で作成し、`finally: report_path.unlink(missing_ok=True)` で削除している設計は原則正しい。
しかし `cmd.extend` でリストを**破壊的変更**していることが問題。
`run_detect` と `run_protect_staged` の両方が `_run_gitleaks` に `cmd` リストを渡している。
呼び出し元が同一リストオブジェクトを再利用するケースは現状ないが、
`cmd.extend(["--report-path", str(report_path)])` の副作用（呼び出し元の `cmd` が変更される）は
設計上の爆弾。Python のリストは参照渡しであり、`_run_gitleaks` が `cmd` を変更することを
呼び出し側のドキュメントに記載がない。

加えて、Windows 環境では `NamedTemporaryFile` で開いたファイルは同プロセス内でも
別ハンドルから書き込めない制限がある（デフォルト `delete=False` でも with ブロック内は排他）。
gitleaks が `--report-path` に書き込む前に with ブロックでファイルを**開いたまま**閉じているか確認が必要。
→ with ブロックを抜けた後 (`tmp` クローズ後) に `cmd.extend` が呼ばれているので gitleaks 書き込み自体は問題ない。
しかし Windows で `NamedTemporaryFile` が作成する 0byte ファイルを gitleaks が上書きできない可能性がある
（Windows のファイルロック問題）。

修正案:
```python
# cmd を変更しないよう新しいリストに結合
full_cmd = cmd + ["--report-path", str(report_path)]
result = subprocess.run(full_cmd, ...)
```
等級: **SE**

---

### [Warning-2] python_analyzer.py:41 — `detect` が全ディレクトリを再帰検索する（大規模リポジトリで性能問題）

```python
return any(project_root.rglob("*.py"))
```

根拠:
`rglob("*.py")` は `.git/`, `node_modules/`, `__pycache__/` 等を含む全ディレクトリを走査する。
大規模リポジトリでは `detect()` 呼び出しだけで数秒のレイテンシが発生する可能性がある。
`any()` でショートサーキットされるため最悪ケースは防ぐが、`.py` ファイルが存在しないモノリポで
全ディレクトリを走査してから False を返す可能性がある。
設計書の非機能要件（解析時間制限）があれば問題になりうる。

修正案:
```python
# プロジェクト直下 1-2 階層のみ確認（ヒューリスティック）
return any(project_root.glob("*.py")) or any(project_root.glob("*/*.py"))
# または除外パターンを追加
```
等級: **SE**

---

### [Warning-3] javascript_analyzer.py:77 — ESLint returncode=2 の警告なしサイレント失敗

```python
if result.returncode not in (0, 1):
    return []
```

根拠:
ESLint の returncode=2 は「設定エラーまたは内部エラー」を意味する（公式ドキュメントより）。
この場合、lint が**実行されていない**にもかかわらず空リストが返る。
呼び出し元（コードレビューパイプライン）は「ESLint が問題を検出しなかった」と誤解する可能性がある。
設計書の「解析失敗時の握り潰し」禁止に抵触する。

修正案:
```python
if result.returncode not in (0, 1):
    if result.stderr:
        logger.warning("eslint failed (returncode=%d): %s", result.returncode, result.stderr[:500])
    else:
        logger.warning("eslint failed with returncode=%d", result.returncode)
    return []
```
等級: **SE**

---

### [Warning-4] rust_analyzer.py:56 — JSON Lines パースの `continue` でエラー行が無音で捨てられる

```python
try:
    entry = json.loads(raw_line)
except json.JSONDecodeError:
    continue
```

根拠:
`cargo clippy --message-format json` は通常 JSON Lines 形式を出力するが、
コンパイルエラーや不正な状態では非 JSON の診断行が混入する。
現状は全ての非 JSON 行を `continue` でサイレントに無視しており、
clippy が重大なコンパイルエラーを出力している場合でも空リストが返る可能性がある。

少なくとも `DEBUG` レベルでスキップ理由をログに残すべき。
さらに、`cargo clippy` がコンパイル自体に失敗した場合（returncode=101）でも
`result.returncode` チェックが存在しないため、0件として扱われる。

修正案:
```python
except json.JSONDecodeError:
    logger.debug("cargo clippy: skipping non-JSON line: %s", raw_line[:100])
    continue
```
また returncode チェックを追加:
```python
if result.returncode not in (0, 1) and not result.stdout.strip():
    logger.warning("cargo clippy failed (returncode=%d)", result.returncode)
    return []
```
等級: **SE**

---

### [Warning-5] gitleaks_scanner.py:183 — `subprocess.run` に `text=False` (デフォルト) だが stderr ログが `len(result.stderr)` のみ

```python
result = subprocess.run(cmd, capture_output=True, timeout=timeout)
logger.debug(
    "gitleaks: exit_code=%d stderr_len=%d",
    result.returncode,
    len(result.stderr),
)
```

根拠:
`text` パラメータを指定していないため `result.stderr` はバイト列 (`bytes`)。
`len(result.stderr)` はバイト数を返すので情報としては正しい。
しかし stderr の内容が DEBUG レベルでもログに出ないため、gitleaks が警告・診断を出した場合に
トラブルシュートが困難になる。
また、gitleaks が `--report-path` にレポートを書けなかった場合（権限エラー等）は
`_parse_gitleaks_json` が空リストを返し（json_path.exists() が False）、スキャン失敗が無音になる。

修正案:
```python
result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
if result.stderr:
    logger.debug("gitleaks stderr: %s", result.stderr[:500])
```
+ `_parse_gitleaks_json` でファイルが存在しない場合の WARNING:
```python
if not json_path.exists():
    logger.warning("gitleaks: report file not created at %s (check permissions)", json_path)
    return []
```
等級: **SE**

---

## Info

### [Info-1] python_analyzer.py:227 — `_build_signature` が `posonlyargs` (Python 3.8+) を無視

根拠:
Python 3.8 以降の位置専用引数 (`def f(a, b, /, c)` の `a`, `b`) は `node.args.posonlyargs` に格納される。
現在のコードは `args.args` のみ反復しており、位置専用引数がシグネチャから欠落する。
AST 解析の精度問題。Phase 2 ツールに置換予定であれば修正は不要だが、現状のコードで
シグネチャが不完全になりうる点は記録に値する。
修正案: `args.posonlyargs` を先頭で処理し、`/` セパレータを追加。
等級: **SE**（修正対応は Phase 2 での tree-sitter 置換時で可）

---

### [Info-2] javascript_analyzer.py:183 — `parse_ast` が空ファイルで `end_line=0` を返す

```python
content = file_path.read_text(encoding="utf-8")
line_count = len(content.splitlines())
```

根拠:
空ファイルの場合 `content.splitlines()` は `[]` を返し `line_count=0` になる。
ASTNode の `end_line=0` は `start_line=1` より小さく、矛盾した状態になる。
`python_analyzer.py` は `max(end_line, 1)` で防いでいるが、JS/Rust の `parse_ast` は未対処。
`rust_analyzer.py` の `parse_ast` (line 211) も同様。

等級: **PG**（`end_line=max(line_count, 1)` の1行修正）

---

### [Info-3] 3アナライザ間の `_SUBPROCESS_TIMEOUT = 300` コピペ

根拠:
`python_analyzer.py:18`, `javascript_analyzer.py:21`, `rust_analyzer.py:19` で同値を定義。
`base.py` や共通定数モジュールへの集約が望ましいが、現状の重複は3箇所のみであり
Rule of Three の「3回」にちょうど達している。設定値変更時の漏れリスクに留意。
過剰抽象化には当たらず、共通定数ファイルへの集約は合理的。
等級: **SE**（リファクタリング候補として記録）

---

### [Info-4] gitleaks_scanner.py — `run_protect_staged` の未インストール時に何もログを出さない

```python
if not is_available():
    return []  # ← ログなし
```

根拠:
`run_detect` は未インストール時に `logger.warning` + Critical Issue を返す（適切）。
`run_protect_staged` は空リストのみ返しログも出ない（設計上の意図的差異と思われるが、
デバッグ時に混乱の元になりうる）。
`INFO` ログ一行でよい。
等級: **PG**

---

## 横断観察

**Silent Failure の一貫性不足**:
3アナライザとも `run_lint` / `run_security` の JSON パース失敗時に空リストを返すパターンを踏んでいる。
`python_analyzer.py` と `javascript_analyzer.py` は `result.stderr` をチェックして WARNING を出す実装だが、
`rust_analyzer.py` の `run_lint` は JSON 行スキップを `continue` のみで処理しており、
全行非 JSON だった場合に完全サイレントになる（Warning-4）。

**subprocess.run のパターン統一**:
`gitleaks_scanner.py` だけ `text=True` を指定しておらず、`result.stderr` がバイト列になっている（Warning-5）。
他3アナライザは `text=True` を正しく指定している。

**命令引数インジェクションリスク**:
4ファイルとも `subprocess.run` はリスト形式（シェル展開なし, `shell=False`）でコマンドを渡しており、
インジェクションリスクは皆無。適切な実装。

**シークレット情報のログ保護**:
`gitleaks_scanner.py` の `_parse_gitleaks_json` は Match/Secret を Issue に格納しない設計が徹底されている。
Critical-1 は例外値の露出という別経路の問題。

**外部ツール未インストール時の挙動**:
- `python_analyzer.py` (ruff/bandit): JSON パース失敗 → 空リスト返却（WARNING あり）
- `javascript_analyzer.py` (npx): returncode チェックで `not in (0, 1)` → 空リスト（WARNING なし）[Warning-3]
- `rust_analyzer.py` (cargo-audit): stdout 空 + returncode!=0 → WARNING あり（returncode=0 空 stdout は Silent）[Critical-2]
- `gitleaks_scanner.py`: `is_available()` 確認 → Critical Issue 返却（最も明示的）
