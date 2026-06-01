# 監査レポート S1: コア hooks

対象: `.claude/hooks/_hook_utils.py`, `pre-tool-use.py`, `post-tool-use.py`, `lam-stop-hook.py`, `pre-compact.py`
日付: 2026-06-01 / Pass 1 whole-project

---

## サマリー

Critical: 3 / Warning: 5 / Info: 3 ／ 評価: **Yellow**

> Critical が存在するため Green State 未達。ただし今すぐ悪用可能な脆弱性ではなく、
> 仕様乖離・セキュリティ境界の抜け道・Silent Failure の三軸に集中している。

---

## Critical

### [Critical] pre-tool-use.py:174 — _read_current_phase の例外を握り潰し、常に "" を返す

```python
    except Exception:
        pass
return ""
```

根拠: フェーズ読み取りが失敗（パーミッションエラー、ファイル破損等）した場合、
AUTONOMOUS フェーズ判定が `"" == "AUTONOMOUS"` となり **FR-9 deny が全スルーされる**。
つまりファイル破損・IO エラーの瞬間に統治ファイルへの書込が通ってしまう。
hook 障害での「Claude ブロック回避」が目的の `except: pass` は適切だが、
FR-9 はセキュリティ境界であり、**フェイルセーフ方向（読み取り失敗＝AUTONOMOUS と仮定して deny）**
にすべきか、または read 失敗をログに残してから "" を返すべき。
現状はサイレントに "" を返すため攻撃面（ファイル破損によるガード回避）になり得る。

修正案:
```python
    except Exception as e:
        # フェーズ読み取りに失敗した場合はセキュリティ安全側（deny 優先）に倒すため
        # ログに記録し、呼び出し側が "UNKNOWN" として扱えるよう識別可能な値を返す
        # （呼び出し元で UNKNOWN を AUTONOMOUS 扱いにするかは PM 判断）
        log_entry(...)  # ただし log_file を引数で受け取る必要あり
        return ""  # または "UNKNOWN"
```
少なくともエラーを stderr に書くことで観測可能性を確保すること。

等級: PM（セキュリティ境界の動作変更。failable-safe か lax どちらかを選ぶ方針決定が必要）

---

### [Critical] lam-stop-hook.py:273-279 — AUTONOMOUS フローで stop_hook_active による再帰防止が機能しない

```python
def _handle_autonomous(input_data, auto_state_file, project_root, log_file):
    stop_hook_active = input_data.get("stop_hook_active")
    _log(log_file, "INFO", f"autonomous flow: stop_hook_active={stop_hook_active}")
    # ← ここで stop_hook_active が True でも _stop() を呼ばずに処理続行
    try:
        state = json.loads(...)
```

根拠: `main()` の STEP 1-2 では `stop_hook_active=true` を最優先に検出して `_stop()` しているが
（line 136-137）、AUTONOMOUS フロー（line 330-331 で分岐）は `_check_recursion_and_state`
を**呼ばずに** `_handle_autonomous` に直行する。`_handle_autonomous` は
`stop_hook_active` を読んでログ出力するだけで再帰ガードを実施していない。

`_block()` の呼び出しが繰り返し re-entry すると Stop hook の無限再帰になり、
Claude Code が「block → stop_hook_active=true → block → ...」のスタックを積む可能性がある。
`stop_hook_active=true` を受け取っても G1 checker を再度起動してしまう。

修正案:
```python
def _handle_autonomous(input_data, ...):
    if input_data.get("stop_hook_active") is True:
        _stop(log_file, "autonomous: stop_hook_active=true → recursion guard exit")
    ...
```
既存の STEP 1 ガードと同じロジックを autonomous フロー冒頭にも追加する。

等級: SE（実装バグ。仕様 design D3 の「再帰防止最優先」と矛盾する）

---

### [Critical] lam-stop-hook.py:277-278 — autonomous_state 読み取り失敗時に _stop() が変数未初期化のまま通過する

```python
    try:
        state = json.loads(auto_state_file.read_text(encoding="utf-8"))
    except Exception:
        _stop(log_file, "autonomous: state read error → normal stop")
    # ← _stop() は sys.exit(0) を送出するため実際には到達しないが、
    #   静的解析は state が未束縛のまま iteration = int(state.get(...)) に
    #   到達する可能性があると判断し、型チェックが通らない
```

根拠: `_stop()` が `sys.exit()` で SystemExit を送出するため実行時は問題ないが、
Python 静的解析（mypy/pyright）は `state` が未定義になるコードパスを検出する。
同構造が `_check_recursion_and_state` にも存在するが（line 143-148）、
そちらは try ブロック成功時のみ後続に進む。`_handle_autonomous` では
`except` ブロックで `_stop()` の返り値（None）の後にそのまま次行が続くよう書かれており、
コードの「意図が明確でない（_stop がnoreturnであると示していない）」問題もある。

修正案:
```python
    except Exception:
        _stop(log_file, "autonomous: state read error → normal stop")
        return  # pylint/mypy 向けに unreachable だが明示的に追加
```
あるいは `_stop()` に `-> NoReturn` 型アノテーションを付ける。

等級: SE（型安全性・保守性の問題。実行時 Critical ではないが誤読・誤修正を誘発するリスク）

---

## Warning

### [Warning] _hook_utils.py:162 — 汎用 Exception catch でデバッグ困難な Silent Failure

```python
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
```

根拠: atomic_write_json の内側 `except Exception` が `raise` で再送出する点は正しい。
しかし直前の `except PermissionError as e` ではクリーンアップ後に `last_error` に保存し
`raise` しないため、PermissionError は退避されてリトライ後にのみ再送出される。
これは意図的な設計であるが、**最終的に `last_error` が None の場合に
`RuntimeError("all retries exhausted")` を送出する**（line 169）。
呼び出し元で `atomic_write_json` の例外をキャッチしているかが不明で、
post-tool-use.py の `_handle_loop_log` では `except Exception: return` で握り潰している（line 265）。
ループ状態ファイルの書き込み失敗が無音で発生する可能性がある。

修正案: `_handle_loop_log` の except ブロックで少なくとも stderr へログを出力する。
```python
    except Exception as e:
        sys.stderr.write(f"loop state write error: {e}\n")
        return
```

等級: SE（Silent Failure。ループ状態の書き込み失敗が検出されない）

---

### [Warning] pre-tool-use.py:43 — _READ_ONLY_TOOLS に書き込み可能ツールが混入する余地の非対称性

```python
_READ_ONLY_TOOLS = frozenset({"Read", "Glob", "Grep", "WebSearch", "WebFetch"})
```

根拠: この frozenset は「常に PG 許可」として機能するが、
将来ツール名が追加された際（例: `Edit`, `Write` が誤って追加された場合）に
FR-9 deny も PM チェックも全スルーになる。
また、`WebSearch`/`WebFetch` はネットワーク通信ツールであり
「read-only」と同一グループに置くことで認識が曖昧になる。

ネットワークツールと読み取りファイルツールをセット名・コメントで分離し、
追加時の意識を高める構造にすべき。

修正案:
```python
_READ_ONLY_FILE_TOOLS = frozenset({"Read", "Glob", "Grep"})
_READ_ONLY_NETWORK_TOOLS = frozenset({"WebSearch", "WebFetch"})
_READ_ONLY_TOOLS = _READ_ONLY_FILE_TOOLS | _READ_ONLY_NETWORK_TOOLS
```

等級: SE（命名・構造の問題。現状では実害なし）

---

### [Warning] post-tool-use.py:119-126 — _read_prev_result の例外握り潰しが FAIL→PASS 遷移を消失させる

```python
def _read_prev_result(last_result_file: Path) -> bool:
    if last_result_file.exists():
        try:
            return last_result_file.read_text(encoding="utf-8").splitlines()[0].startswith("fail")
        except Exception:
            pass
    return False
```

根拠: 前回失敗結果ファイルの読み取りが IO エラー等で失敗した場合、
`prev_was_fail = False` として扱われる。この場合 FAIL→PASS の遷移が記録されず、
TDD 内省パイプラインの `systemMessage` 通知が抑制される。
ユーザーは `/retro` の推奨を受けられず、パターン分析機会を逃す。
`except Exception: pass` は機能的に無音であり Code Quality Guideline の
「Error Swallowing」に該当する。

修正案:
```python
        except Exception as e:
            sys.stderr.write(f"last-test-result read error: {e}\n")
            pass
```
少なくともエラーを stderr に出力し観測可能にする。

等級: SE（TDD パイプラインの機能的サイレント劣化）

---

### [Warning] lam-stop-hook.py:199-212 — PreCompact 時刻パース失敗の内側 except が pass で沈黙

```python
    except Exception:
        try:
            flag_mtime = os.path.getmtime(str(pre_compact_flag))
            ...
        except Exception:
            pass
```

根拠: 最内 `except Exception: pass` は ISO パース失敗 → mtime フォールバック失敗という
二重失敗ケース。この場合 PreCompact が実際には直近に発火していても「無視」されて
ループが継続する可能性がある。コンテキスト枯渇後の無限ループリスクに繋がる。

修正案: 少なくとも外側 except の冒頭で stderr に書く。

等級: SE（コンテキスト枯渇の検出失敗でループ安全ネットが機能しない）

---

### [Warning] pre-compact.py:96-98 — 全 Exception を握り潰して常に exit 0

```python
    except Exception:
        # 圧縮をブロックしないため常に正常終了
        pass
```

根拠: 設計意図（圧縮ブロック禁止）は正しい。しかし SessionState 書き込み失敗・
バックアップ失敗が完全に無音になるため、コンテキスト圧縮直後にループ状態が
失われても誰も気づかない。`safe_exit(0)` の前に stderr への最低限のログが必要。

修正案:
```python
    except Exception as e:
        sys.stderr.write(f"pre-compact error (non-fatal): {type(e).__name__}: {e}\n")
```

等級: SE（フェイルサイレントだが診断不能。状態ロストに気づけない）

---

## Info

### [Info] _hook_utils.py:51-62 — read_stdin_json が EOF・空入力を空 dict で返す際の呼び出し側の振る舞い

根拠: 空 dict が返ると tool_name が空文字になり、pre-tool-use.py では SE 扱いで exit 0。
post-tool-use.py では 3 つのハンドラすべてで早期リターン条件を満たす。
これは現状では問題ないが、「空 dict → 何も起きない」という挙動を
コメントで明示しておくと保守性が上がる（現状は呼び出し側を読まないと分からない）。

等級: Info

---

### [Info] post-tool-use.py:64-71 — _get_test_cmd_label がフォールバックで "pytest" を返す

根拠: `make test` コマンドはチェックするが `gotestsum` 等の go 系ラッパーを含む
カスタムコマンドが入力された場合、`"pytest"` ラベルが誤ってログに記録される。
現状のテストコマンドセットは限定的で大きな問題ではないが、
フォールバックを `"pytest"` ではなく `command[:20]` 等の実コマンド由来にする方が
tdd-patterns.log の可読性が上がる。

等級: Info

---

### [Info] lam-stop-hook.py:115-117 — _save_loop_log の内部 except が pass で沈黙

```python
    except Exception:
        pass
```

根拠: ループ終了ログの書き込み失敗は副作用であり、stop の判断には影響しない。
設計上 pass は許容範囲だが、他の Silent Failure と一貫してエラーを stderr に書くべき。

等級: Info

---

## 横断観察

### 1. Silent Failure の一貫性不足

`pre-tool-use.py` の最外 `except Exception: sys.exit(0)` はコメント付きで意図明確（Claude ブロック回避）。
しかし各関数内部の `except Exception: pass` は「なぜ無音か」のコメントが薄く、
セキュリティ境界の関数（`_read_current_phase`）でさえ同パターンで書かれている。
「フック障害では exit 0」という設計原則を **関数レベルの例外まで適用するべきか、しないべきか**
の方針が統一されていない。推奨: 「フック障害 = main レベルでのみ握る。内部関数は記録して再 raise」。

### 2. FR-9 二重防御の層1（settings.json）が T1-5 未実装

コメント・docstring に「層1は T1-5 後に実装」と複数箇所に記載されている
（pre-tool-use.py line 16-17, 91-92）。現状は層2（プロンプティング）のみ有効。
T1-5 が未着手のまま AUTONOMOUS モードが有効化された場合、
`_read_current_phase` の Critical 指摘（ファイル破損→フェーズ検出失敗）と組み合わさると
FR-9 の二重防御が機能せず、統治ファイルへの書込が通ってしまう。
T1-5 の優先度を上げることを推奨する（アーキテクチャ上の未完成。PM 確認推奨）。

### 3. autonomous_state.py は監査対象外だが lam-stop-hook.py と密結合

`lam-stop-hook.py` は `autonomous_state` を top-level import（line 48）している。
`autonomous_state.py` 読み込み失敗時（ファイル破損等）は `main()` 到達前に
`ImportError` が発生し、最外 `except Exception: sys.exit(0)` で握られる。
これは設計通り（hook 障害 → Claude ブロックしない）だが、
autonomous モードが有効な状態でこれが発生すると **Stop hook が何もせず通過**する。
つまり G1 checker が一切実行されずに completion が許可される。設計上の想定かを確認すること。
