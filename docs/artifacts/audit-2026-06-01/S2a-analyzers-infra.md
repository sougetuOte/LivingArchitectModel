# 監査レポート S2a: analyzers 基盤

対象: `.claude/hooks/analyzers/` 9 ファイル  
日付: 2026-06-01 / Pass 1  
監査官: read-only コード品質監査 (S2a)

---

## サマリー

| 区分 | 件数 |
|------|------|
| Critical | 1 |
| Warning | 5 |
| Info | 3 |

**評価: Yellow**（Critical 1 件 → Green State 未達）

---

## Critical

### [Critical] run_pipeline.py:162 — analyzers が空の場合に line_count=0 を返し、scale_detector.py と count_lines() の呼び出し経路が分岐する（Silent Failure）

```python
line_count = count_lines(project_root, config.exclude_dirs) if analyzers else 0
```

`analyzers` が空（対象言語なし）のとき `line_count = 0` に固定される。
`run_phase0` は `Phase0Result(line_count=0, ...)` を返し、呼び出し元がこの 0 を「本当に空プロジェクト」と区別できない。
一方 `scale_detector.py:158` では同じ `config` を受け取っても無条件で `count_lines()` を呼ぶ。
結果として同一プロジェクトに対して `run_phase0` と `detect_scale` が異なる `line_count` を返す可能性があり、
スケール判定（Plan A/B/C/D の有効化）と Phase 0 の行数記録が食い違う。

- 根拠: Error Swallowing / Silent Failure — 「0」は情報損失であり、呼び出し元が誤判定するリスク
- 修正案:
  1. `analyzers` の有無に関わらず `count_lines()` を常に呼ぶ（最小コスト）
  2. または `Phase0Result` に `line_count_skipped: bool` フラグを追加して呼び出し元が区別できるようにする
- 等級: **SE**（内部ロジック変更、公開 API は `Phase0Result` dataclass のみ）

---

## Warning

### [Warning] chunker.py:132–157 — `_trim_header` / `_trim_footer` が完全な重複実装（Rule of Three 超過）

`_trim_header` と `_trim_footer` は関数名・docstring を除いてコードが 1 行も違わない。
`_trim_overlap` (chunker.py:160) の内部から両方が呼ばれ、振る舞いの違いはない。
将来の変更時に片方だけ修正されるドリフトリスクがある。

- 根拠: Duplication — 同一実装が 2 箇所（Rule of Three 規定「3 回以上」には達しないが、
  コードパスとして完全同一なためより厳格に判定）
- 修正案: `_trim_overlap_text(text: str, max_tokens: int) -> str` に統一し、
  `_trim_header`/`_trim_footer` を薄いラッパーか呼び出し側の直接呼び出しに置き換える
- 等級: **SE**（内部リファクタ、公開 API の `chunk_file()` は不変）

---

### [Warning] chunker.py:17–24 — `ImportError` のみキャッチで `tree_sitter.Language()` の実行時エラーが未捕捉

```python
try:
    import tree_sitter
    import tree_sitter_python
    _PYTHON_LANGUAGE = tree_sitter.Language(tree_sitter_python.language())
    _TREE_SITTER_AVAILABLE = True
except ImportError:
    _TREE_SITTER_AVAILABLE = False
```

`tree_sitter.Language(...)` はインポート後に呼ばれるため、
`ImportError` 以外（`AttributeError`, `RuntimeError`, `OSError` 等）で失敗した場合は
モジュールロード時に未処理例外が発生し、`analyzers` パッケージ全体がロード不能になる。
環境によっては tree-sitter の ABI 不一致で `RuntimeError` が発生することが知られている。

- 根拠: Error Swallowing の逆 — 本来は `_TREE_SITTER_AVAILABLE = False` で fallback するべき
  例外が上位に漏れる
- 修正案: `except (ImportError, Exception)` に拡大し警告ログを出す
  （または `except Exception as e: logger.warning(...); _TREE_SITTER_AVAILABLE = False`）
- 等級: **SE**

---

### [Warning] base.py:147–159 — `_load_module` が `RuntimeError` / `TypeError` / `ModuleNotFoundError` を捕捉しない

```python
except (ImportError, OSError, AttributeError, ValueError) as e:
```

`exec_module` が発生させうる例外は上記以外に `RuntimeError`（ABI 不一致等）、
`TypeError`（Analyzer コンストラクタの誤定義）、`ModuleNotFoundError`（間接依存の欠如）がある。
これらは捕捉されず上位スタックに伝播し、`auto_discover` 呼び出し元でパイプライン全体が停止する。

- 根拠: Error Swallowing の逆（未捕捉例外）— Analyzer を動的ロードする場合は
  `except Exception` で囲み警告ログを出すのが通例
- 修正案: `except (ImportError, OSError, AttributeError, ValueError, RuntimeError, TypeError)` に拡大するか、
  シンプルに `except Exception`（理由をコメントに記す）
- 等級: **SE**

---

### [Warning] state_manager.py — `save_issues` / `save_ast_map` / `save_file_hashes` / `save_chunk_result` / `save_chunks_index` / `save_dependency_graph` に書き込み失敗時の例外処理がない（6 箇所）

永続化系の `save_*` 関数はいずれも `Path.write_text()` / `json.dumps()` をそのまま呼び、
`OSError`（ディスク満杯・権限不足等）が発生した場合に呼び出し元まで例外が伝播する。
対応する `load_*` 関数はすべて `try/except json.JSONDecodeError` を持ちフォールバックするが、
`save_*` 側の一貫性がない（非対称な信頼性設計）。

- 根拠: 部分失敗の握りつぶしとは逆だが、書き込み失敗が上位のパイプライン全体を
  停止させる可能性がある。state_manager は「障害回復を担う層」であるため、
  書き込み失敗を warning ログに留めてパイプラインを続行できるべき
- 修正案: 各 `save_*` に `try/except OSError as e: logger.warning(...)` を追加し、
  失敗をサイレント継続させるかどうかは呼び出し側設計に委ねる
- 等級: **SE**

---

### [Warning] orchestrator.py:344–357 — `collect_results` が失敗チャンクの Issue 損失を無言で受理する

```python
for r in results:
    if r.success:
        batch.succeeded += 1
        batch.all_issues.extend(r.issues)
    else:
        batch.failed += 1
        batch.failed_chunks.append(r.chunk_name)
```

`success=False` の `ReviewResult` は `r.issues` を破棄する。
設計上は「失敗したチャンクの Issue は収集しない」意図と思われるが、
LLM エラー以外の理由（部分的 parse 失敗等）で `success=False` かつ `issues` に
部分結果が格納されているケースで情報損失が起きる。
また、`failed_chunks` は chunk_name のリストであり、再実行の起点として不十分
（`file_path` が含まれない）。

- 根拠: Dead Code に近い情報損失 — `r.issues` が存在しても無視される経路
- 修正案:
  1. `r.issues` が空でない場合は `batch.all_issues.extend(r.issues)` する（部分結果を保持）
  2. `failed_chunks` に `(chunk_name, file_path, error)` のタプルを格納し再実行を可能にする
- 等級: **SE**

---

## Info

### [Info] config.py:29–65 — `ReviewConfig.load` が不正なフィールド値（型ミスマッチ）を無言で default に fallback する

`data.get("max_parallel_agents", defaults.max_parallel_agents)` 等は
JSON に `"max_parallel_agents": "four"` のような文字列が入った場合に
デフォルト値を返さず文字列をそのまま採用する（`isinstance` チェックがない）。
`gitleaks_enabled` だけが `_parse_bool` で厳格にチェックされており一貫性がない。

- 根拠: Info — 動作上は問題が出るまで気づかない可能性があるが、
  バグとして顕在化するのはパイプライン実行時のみ。型チェックを全フィールドに統一することで
  設定ミスの早期発見が可能
- 等級: SE

---

### [Info] orchestrator.py:284 — `build_review_prompt_with_contracts` 内の遅延 import

```python
from analyzers.card_generator import format_contract_cards_for_prompt
```

呼び出し時に毎回モジュールを解決する遅延 import。Python はインポートキャッシュを持つため
パフォーマンスへの影響は軽微だが、循環インポート回避の意図なら TYPE_CHECKING ブロックに
移動して明示化した方が読みやすい。

- 等級: SE（微改善）

---

### [Info] scale_detector.py:191–228 — `format_scale_detection` と `_persist_result` が同一モジュール内にあるが設計上の責務が異なる

`format_scale_detection`（表示）と `_persist_result`（永続化）は
`detect_scale`（判定）と同じファイルに混在している。
他の永続化ロジックは `state_manager.py` に集約されており、
`_persist_result` のみ `scale_detector.py` に置かれているのは設計上の非一貫性。

- 等級: SE（将来的なリファクタリング候補）

---

## 横断観察

1. **エラー処理の非対称性**: `load_*` 系は全て `try/except json.JSONDecodeError` で保護されているが、
   `save_*` 系に同等の保護がない。load/save ペアで信頼性設計を揃えることを推奨。

2. **`count_lines` の二重呼び出しリスク**: `run_pipeline.run_phase0` と `scale_detector.detect_scale` が
   それぞれ独立して `count_lines(project_root, config.exclude_dirs)` を呼ぶ。
   大規模プロジェクトでは `rglob("*")` のコストが問題になりうる。
   `Phase0Result.line_count` を `detect_scale` に渡すか、
   共有キャッシュを `state_manager` に置く設計を検討すること。

3. **`_trim_header` / `_trim_footer` の完全同一性**: コードの重複を超えて、
   「header と footer で切り詰め戦略が同一で良いか」という設計判断の表明が欠如している。
   footer は「削っても文脈が失われにくい情報」として後から切ることが設計書上の意図だが、
   その意図が関数名の違いだけで表現されており脆い。

4. **`analyzers/__init__.py` が空**: パッケージの公開 API（`__all__`）が定義されていない。
   現状は問題ないが、将来的に外部から `from analyzers import *` された場合の挙動が未定義。
