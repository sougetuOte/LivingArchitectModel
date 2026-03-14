# 監査統合レポート（イテレーション 1）

**日時**: 2026-03-14
**対象**: `.claude/hooks/analyzers/`（ソース 8 ファイル + テスト 9 ファイル）
**ブランチ**: `review/analyzers-self-review`
**エージェント**: ソースコード品質 / テストコード品質 / アーキテクチャ・仕様整合性 / セキュリティ（全4完了）

## サマリー

| 重要度 | 件数 |
|--------|------|
| Critical | 9 件 |
| Warning | 18 件 |
| Info | 10 件 |
| **合計** | **37 件** |

| 権限等級 | 件数 |
|---------|------|
| PG | 4 件（自動修正可） |
| SE | 25 件（修正後報告） |
| PM | 8 件（承認必要） |

---

## PM級 Issues（承認必要 — 8件）

### [PM-1] base.py:136-141 — auto_discover の任意コード実行リスク [High/Security]
`auto_discover()` は `*_analyzer.py` を動的にロード・実行。悪意のあるリポジトリに `evil_analyzer.py` を配置されると任意コード実行が可能。
**修正案**: (A) 自プロジェクト内に限定 (B) ホワイトリスト検証 (C) auto_discover 無効化オプション

### [PM-2] C-1 と関連 — language_name プロパティ追加は公開インターフェース変更
`LanguageAnalyzer` ABC に `language_name` 抽象プロパティを追加すると全サブクラスに影響。
**修正案**: 仕様書更新も同時に必要

### [PM-3] 仕様ドリフト: semgrep が仕様に記載されているが未実装（FR-1）
仕様書 FR-1 の初期サポート言語表に Python/JS 両方で `semgrep` が明示されているが、実装なし。
**修正案**: (A) semgrep 実装追加 (B) 仕様書から除外し「Phase 2 以降」と明記

### [PM-4] 仕様ドリフト: run_all() が設計書の「並列実行」と異なり逐次実装
設計書 Section 2.1b で「lint + security を並列実行」と記述されているが、実装は逐次 for ループ。
**修正案**: (A) ThreadPoolExecutor で並列化 (B) 設計書を「逐次実行」に訂正

### [PM-5] 仕様ドリフト: run_phase0() でファイルハッシュキャッシュが未利用（FR-5）
FR-5「未変更ファイルの静的解析結果はキャッシュを利用」が未実装。state_manager.py には実装済みだが未呼び出し。
**修正案**: (A) run_phase0() にキャッシュロジック追加 (B) 仕様書に「Phase 1 スコープ外」と明記

### [PM-6] C-3/state_manager.py — generate_summary() が NFR-4 構造に非準拠
設計書のサマリー配置順と実装が不一致。「レビュー指示」ブロック欠落。
**修正案**: 実装修正 or 仕様書の配置定義を実装に合わせて更新

### [PM-7] 仕様ドリフト: semgrep が JS Analyzer にも欠落（D-2）
PM-3 と同根。JS 側でも semgrep + npm audit のうち semgrep が未実装。

### [PM-8] 仕様ドリフト: run_all() の並列実行 — FR-1「複数言語混在時: 全言語を並列実行」との乖離
PM-4 と同根だが FR-1 仕様側からの指摘。NFR-5 実行時間目標への影響。

---

## Critical Issues（SE級 — 6件）

### [C-1] run_pipeline.py:114 — 言語除外フィルタがクラス名文字列変換に依存 [SE]
`replace("analyzer", "")` で言語名を特定しており壊れやすい。PM-2 と連動。
**修正案**: `language_name` プロパティで解決

### [C-2] run_pipeline.py:106 — auto_discover で組み込み Analyzer が重複登録 [SE]
手動登録後に同じディレクトリを `auto_discover()` に渡し、3 Analyzer が 2 度インスタンス化される。
**修正案**: `auto_discover()` に重複チェック追加、または手動登録を除去して自動探索に統一

### [C-3] state_manager.py:57-85 — generate_summary() が NFR-4 構造に非準拠 [SE]
Issue 0 件のセクションも空ヘッダーが残る。「レビュー指示」「FR-5 リマインド」セクション欠落。
**修正案**: Issue 0 件セクションスキップ + レビュー指示ブロック追加

### [C-4] test_javascript_analyzer.py:550 — アサーションが常に真になる論理バグ [SE]
`or` の右辺で `len(call_args.args) == 0` が真になるため `cwd` 検証をスキップ。
**修正案**: `call_args[1].get("cwd") == tmp_path` で直接検証

### [C-5] test_run_pipeline.py:166-170 — test_no_languages_detected が subprocess 未モック [SE]
fixture の副産物で通過。将来 fixture 変更で無音で壊れる。
**修正案**: 完全に空の `tmp_path` を使用

### [C-6] test_run_pipeline.py:172-180 — shutil.which のモックターゲットが不正確 [SE]
`patch("shutil.which")` ではなく `patch("analyzers.base.shutil.which")` であるべき。
**修正案**: モックターゲット修正（test_registry.py:244-287 も同様）

---

## Warning Issues（18件）

### PG級（4件）
| ID | ファイル | 内容 |
|----|---------|------|
| W-1 | python_analyzer.py:70-79 | ruff severity "warning" 固定にコメントなし |
| W-3 | run_pipeline.py:43-57 | `exclude_dirs=[]` vs `None` の挙動差異 → `is not None` に修正 |
| W-6 | state_manager.py:67 | 行長 101 文字超過（E501） |
| W-9 | test_config.py | テストメソッドに `-> None` 型アノテーション欠落 |

### SE級（14件）
| ID | ファイル | 内容 |
|----|---------|------|
| W-2 | base.py:29 | severity/category が str で型安全でない → StrEnum 化 |
| W-4 | rust_analyzer.py:196-207 | cargo-audit の shutil.which 検出不可 → `cargo audit --version` で検証 |
| W-5 | javascript_analyzer.py:101-113 | run_security() の cwd がディレクトリ前提 |
| W-7 | config.py:36-58 | ReviewConfig.load() の手動フィールドマッピング |
| W-8 | test_base.py:77-95 | severity 不正値テストの欠如 |
| W-10 | test_run_pipeline.py:120-139 | assert len >= 1 が弱すぎる → == 1 |
| W-11 | test_run_pipeline.py:186-209 | ヘルパー関数の配置が不統一 |
| W-12 | test_python_analyzer.py:190-195 | テスト名と実際の挙動の乖離 |
| W-13 | config.py:29-58 | ReviewConfig.load() の型バリデーション欠如 |
| W-14 | base.py:121 vs design.md | フィールド名 `_analyzer_classes` vs `_analyzers` 不一致 |
| W-15 | design.md:317 vs config.py:16 | デフォルトチャンクサイズ 4000 vs 3000 不一致 |
| W-16 | base.py:162-173 | `--version` バージョン互換チェック未実装（D-3/D-6） |
| W-17 | run_pipeline.py:104-106 | auto_discover のインポートパス曖昧性 |
| W-18 | test_run_pipeline.py:46-64 | テスト期待値が `_CODE_EXTENSIONS` 変更に追従しない |

---

## Info Issues（10件）
| ID | ファイル | 内容 | 等級 |
|----|---------|------|------|
| I-1 | base.py:133-150 | _load_module の例外未キャッチ | SE |
| I-2 | run_pipeline.py:140-141 | 重複 mkdir 呼び出し | PG |
| I-3 | python_analyzer.py:31-35 | rglob の大規模プロジェクト性能 | SE |
| I-4 | python_analyzer.py:55-56,94-95 | stderr そのまま出力（情報露出） | SE |
| I-5 | tests/test_registry.py:160-177 | auto_discover テストで実コード実行 | SE |
| I-6 | __init__.py | 空ファイル（re-export なし） | PG |
| I-7 | test_state_manager.py | 削除ファイル検出テスト欠如 | SE |
| I-8 | test_run_pipeline.py:73-95 | 境界値 9999 テスト欠如 | SE |
| I-9 | conftest.py:19-24 | project_root fixture の用途不明瞭 | PG |
| I-10 | full-review.md Phase 0 Step 3 | 接続手順が非具体的 | Info |
