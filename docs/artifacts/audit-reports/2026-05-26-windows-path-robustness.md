# 監査レポート: Windows パス処理の堅牢性 + テスト環境整合性

**日付**: 2026-05-26
**対象**: `.claude/hooks/` 全般（`_hook_utils`, `pre-tool-use`, `analyzers/`）+ テスト依存環境
**契機**: 2ヶ月ぶりの再開時にテスト3件が失敗。根本原因調査の過程で関連バグ群を発見。

## サマリー

- 検出項目数: 6件
- **Critical: 1件** / **Warning: 3件** / **Info: 2件**
- 総合評価: **B**（実害バグを修正済み。残課題は堅牢性・テスト衛生の改善提案）
- テスト: 575 passed / 5 deselected（修正後・全グリーン）

## Critical Issues

### [C-1] Windows でパス区切りが `\` のまま流れ、セキュリティ境界とモジュール検出をすり抜ける

- **場所**:
  - `_hook_utils.py:normalize_path`（絶対パス分岐 + 相対パス分岐）
  - `analyzers/python_analyzer.py:56` / `analyzers/javascript_analyzer.py:89`（`str(Path.relative_to())`）
- **内容**: いずれも `str(relative)` で Windows のバックスラッシュ区切り文字列を返していた。消費側は `/` 区切り前提：
  - `pre-tool-use.py` の `_PM_PATTERNS`（`^docs/specs/.*\.md$` 等）→ `docs\specs\x.md` がマッチせず **PM級保護をすり抜け、SE級に誤分類**（仕様・ルールファイルの承認ゲートが Windows で無効化）。
  - `card_generator.py` の `_assign_files_to_modules` 等は `fp.split("/")` に全面依存 → `Issue.file` に `\` が混入すると `len(parts) <= 1` 分岐で全ファイルがスキップされ、**モジュール境界検出が全崩壊**（scalable-code-review の出力品質が劣化）。
- **データフロー（確認済み）**: analyzer の `_relativize_path` → `Issue.file` → `card_generator` の `file_paths` → `split("/")`。
- **推奨対応**: `str(relative)` → `relative.as_posix()` に統一。**→ 修正済み（SE級）**。`normalize_path` の相対分岐も `p.as_posix()` 化。回帰テスト 1件追加（Windows 限定 skipif）。

## Warnings

### [W-1] `card_generator.py` の `split("/")` 依存（防御的堅牢性）
- **場所**: `card_generator.py:518,520,539,559,564,570,672`
- **内容**: C-1 の発生源（analyzer）は修正したが、`file_paths` の入力規約が「必ず POSIX 形式」であることはコード上保証されていない。将来別経路から `\` パスが供給されると再発する。
- **推奨対応**: `detect_module_boundaries` の入口で `fp.replace("\\", "/")` 正規化、または入力規約を docstring/型で明示。**未修正（要承認: SE級だが released feature のため checkpoint）**。

### [W-2] tree-sitter 任意依存テストが skip せず hard-fail
- **場所**: `analyzers/tests/test_chunker.py`（19件）, `test_e2e_review.py::TestScaleDetection`（1件）
- **内容**: 設計（`scalable-code-review-design.md` §3.0）では tree-sitter は**任意依存・グレースフルデグレード**前提で「pyproject に必須依存として追加しない」と明記。一方テストは未インストール時に `skipif` せず例外/アサーション失敗する。dev 環境で full suite を回すには未宣言の追加 pip install が必要、という不整合。
- **推奨対応**: 該当テストに `@pytest.mark.skipif(tree_sitter 未導入)` を付与、**または** dev テスト依存を `requirements-dev.txt`/CONTRIBUTING に明文化。pyproject への必須依存追加は設計違反のため不可。**未修正（要承認）**。

### [W-3] テスト依存の宣言ギャップ（再現性）
- **場所**: `requirements-dev.txt`（`pytest>=7.0` のみ）
- **内容**: analyzers は実行に `tree-sitter`, `tree-sitter-python`（Python import）と `ruff`, `bandit`（外部CLI, `shutil.which` 検出）を要する。いずれも宣言されておらず、クリーン環境では full suite が再現しない。
- **推奨対応**: dev 用に `requirements-dev.txt` へ `tree-sitter` 系を追記（任意依存と矛盾しない範囲で「テスト実行に推奨」と注記）、または `docs/internal/04_RELEASE_OPS.md` に手順記載。**未修正（要承認）**。

## Info

### [I-1] `test_integration_pipeline.py:400` の `split("/")`
テストコード内 `file_path.split("/")[-1]` も Windows で `\` 混入時に脆い。現状は POSIX 固定値入力のため顕在化せず。

### [I-2] javascript/rust analyzer は Phase 1 スタブ
tree-sitter-javascript / tree-sitter-rust は現状未使用（children 空のスタブ）。Phase 2 で AST 置換予定。今回 venv には未導入で問題なし。

## Documentation Sync Status
- specs: ✓（`scalable-code-review-spec.md` の任意依存方針と実装は一致）
- design: ✓（§3.0 のグレースフルデグレード方針と実装は一致）
- adr: 該当なし
- tasks: ✓（cross-module-blame は全タスク完了済み）

## 推奨アクション
1. **【完了・要報告】** C-1 のコード修正（`_hook_utils` x2 + analyzers x2 + 回帰テスト1）。SE級。
2. **【要承認】** W-1: `card_generator` 入口でのパス正規化（防御的）。
3. **【要承認】** W-2/W-3: tree-sitter 任意依存のテスト skip 化 or dev依存の明文化（どちらの方針か判断仰ぐ）。
4. **【判断のみ】** C-1 は Windows 環境で **PM級承認ゲートが無効化されていた**重大バグ。リリース済み（v4.6.1）への影響として CHANGELOG 追記 + パッチリリース（v4.6.2）を検討。
