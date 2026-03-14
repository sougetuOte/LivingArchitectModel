# auto_discover の任意コード実行リスク対策

**起票日**: 2026-03-14
**起源**: full-review self-review (2026-03-14-analyzers-iter1.md PM-1)
**優先度**: Medium（現状は自プロジェクト限定のため低リスク）
**対象 Phase**: Phase 2 以降

## 問題

`AnalyzerRegistry.auto_discover()` は `*_analyzer.py` を動的にロード・実行する。
外部リポジトリに対して `run_phase0()` を実行する場合、悪意のある `evil_analyzer.py` が
配置されていると任意コード実行が可能。

## 現状のリスク

- `run_phase0()` は自プロジェクトの `.claude/hooks/analyzers/` のみを対象
- CI/CD で外部リポジトリを処理するユースケースは未実装
- リスクは将来の拡張時に顕在化する

## 修正案

1. `auto_discover()` の適用を自プロジェクトパスに限定するホワイトリスト検証
2. 外部リポジトリ処理時に `auto_discover` を無効化するオプション
3. `search_dir.resolve()` と `project_root.resolve()` のパストラバーサル検証

## 対応条件

Phase 2 以降で外部リポジトリ対応を実装する際に同時対応すること。
