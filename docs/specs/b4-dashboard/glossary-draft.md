# 用語集（暫定）: b4-dashboard

- バージョン: 0.2.0
- 作成日: 2026-06-20
- 更新日: 2026-06-20（Q1〜Q5 PM 回答反映・軽微指摘対応）
- ステータス: 設計フェーズ着手可（Q1〜Q5 解決済み）

> **注意**: Q1〜Q5 への PM 回答が 2026-06-20 に得られ、以下の確定事項が反映済み。
> `.claude/rules/terminology.md` と矛盾する定義は記載しない。
> 本ファイルは terminology.md の補強・拡張のみを目的とする。

---

## §1 階層名（用語ガイドラインとの対応）

以下は `.claude/rules/terminology.md` §1 で定義された用語を b4-dashboard の文脈で具体化したもの。
定義の権威は terminology.md にあり、本ファイルは補足説明のみを提供する。

| b4-dashboard での呼称 | terminology.md での位置 | b4-dashboard スコープでの意味 |
|----------------------|------------------------|------------------------------|
| Project | 最上位 | LAM（Living Architect Model）。現時点では 1 件のみ（Q3=B 確定: V-1 はトップサマリーページ）|
| Milestone | Project 直下 | B-4、B-5 等のマイルストーン。ダッシュボード V-2 で表示 |
| Step | Milestone 直下 | PLANNING / BUILDING / AUDITING 等。V-2 の「現在の Step」属性列として表示（独立ビューなし・Q2=B 確定）|
| Wave | Step 直下 | Wave 1、Wave 1.5 等。ダッシュボード V-3 で表示 |
| Task | Wave 直下 | PR-A、PR-B、W7-B4-T9 等。ダッシュボード V-4 で表示 |
| Phase | 補助（規律） | PLANNING / BUILDING / AUDITING フェーズ規律。`.claude/current-phase.md` で管理 |

### 「個別実行ループ」について（確定: Q1=D・2026-06-20）

SESSION_STATE.md §5 の「5 階層モデル」に記載された「個別実行ループ」は、
terminology.md の Task に統合されることが確定した（Q1=D）。
本スコープでは独立した定義・ビューを設けない。
SESSION_STATE.md の旧記述は terminology.md §5 移行猶予条項により温存される（修正不要）。

---

## §2 状態名

b4-dashboard で使用する状態値の定義（`requirements.md` FR-2 と対応）。

| 状態値 | 表示ラベル（暫定）| 意味 |
|-------|-----------------|------|
| `not-started` | 未着手 | 着手が確認されていない状態。tasks.md の未チェック項目、SESSION_STATE の未記載項目 |
| `in-progress` | 進行中 | 着手済みで未完了。SESSION_STATE.md の「進行中タスク」セクションに記載のある項目 |
| `blocked` | ブロック中 | 前提条件未充足・未解決質問あり・外部依存待ち等で進行できない状態 |
| `completed` | 完了 | git commit または SESSION_STATE の「完了タスク」セクションへの記録により確認できる状態 |

### 状態値の決定ロジック（暫定・設計フェーズで確定）

1. SESSION_STATE.md の「完了タスク」セクションに記載あり → `completed`
2. SESSION_STATE.md の「進行中タスク」セクションに記載あり → `in-progress`
3. SESSION_STATE.md の「未解決の問題」に記載あり → `blocked`
4. tasks.md に記載あるが 1〜3 いずれにも該当しない → `not-started`

> **Q5=D 確定（2026-06-20）**: データソース間の競合は発生しない設計（ビュー単位でデータソース固定）。
> 各ビュー V-1〜V-4 は §3 のデータソース対応表に従い、ビューごとに参照データソースが一意に決まる。
> 同一項目を複数データソースから取得して競合解決するロジックは持たない（GitHistory は V-3 の補完情報のみ・Q5=D）。

---

## §3 データソース名

ダッシュボードが参照するファイル群の識別名（`requirements.md` FR-4 と対応）。

| 識別名 | 実体ファイル | 取得情報 | 対応ビュー |
|--------|-----------|---------|----------|
| SessionState | `SESSION_STATE.md` | 現在フェーズ・進行中タスク・完了タスク・未解決問題・次ステップ | V-2, V-3 |
| CurrentPhase | `.claude/current-phase.md` | 現在のフェーズ（PLANNING / BUILDING / AUDITING）| V-2（Step 属性列）|
| MilestoneTasks | `docs/specs/<milestone>/tasks.md` | タスク一覧・完了チェック状況（checkbox 形式）| V-4 |
| GitHistory | `git log` 出力（コマンド出力。ファイルパスではない）| コミット履歴（Wave・Task 完了の補完情報）| V-3（補完のみ）|

> **確定事項（PM 回答: 2026-06-20・Q5=D）**: GitHistory は V-3 の補完情報としてのみ使用する。
> データソースの識別名は設計フェーズで最終確定する。

---

## §3.5 プロセス名（暫定）

b4-dashboard で使用するプロセス（処理）の暫定名称。UI 要素ではなく実行処理の概念名。

| 暫定名称 | 意味 |
|---------|------|
| ビルド | データソースを読み込み HTML ファイルを生成する処理（design フェーズでスクリプト名を確定）|

> **移設注記**: 「ビルド」は旧 §4（UI 要素名）に分類されていたが、UI 要素ではなく処理（プロセス）であるため独立節に移設（2026-06-20）。

---

## §4 UI 要素名（暫定）

b4-dashboard の成果物（単一 HTML ファイル）で使用する UI 要素の暫定名称。
具体的な HTML 要素・CSS 設計は design フェーズの責任範囲であり、本節は要素の概念名のみを定義する。

| 暫定名称 | 意味 |
|---------|------|
| ダッシュボード | 生成される単一 HTML ファイル全体 |
| ビュー | ダッシュボード内の表示単位（V-1〜V-4）|
| ビュー V-1 | Project サマリービュー（最上位・LAM 単一プロジェクト固定）|
| ビュー V-2 | Milestone 一覧ビュー |
| ビュー V-3 | Wave 一覧ビュー |
| ビュー V-4 | Task 一覧ビュー |
| ステータスバッジ | 状態値（§2）を視覚的に示すラベル要素（色・テキスト）|
| ドリルダウン | V-1 → V-2 → V-3 → V-4 の順で詳細を掘り下げるナビゲーション操作 |

---

## §5 スキル名（暫定）

b4-dashboard 実装に伴い追加予定のスキル（仮称。設計フェーズで確定）。

| 仮称 | 役割 |
|------|------|
| `/visualize` | ダッシュボード HTML を生成するスキル（`requirements.md` FR-10 に対応）|

> スキル名・フロントマター書式は `.claude/skills/` 内の既存スキルに合わせて設計フェーズで確定する。
> `/visualize` はあくまで仮称であり、確定前に実装で使用してはならない（MUST NOT）。

---

## §6 将来候補（暫定語）

以下の用語は requirements.md の Non-Goals または future-candidates に対応する概念であり、
本段階では定義を行わない。将来フェーズで定義を追加する。

| 暫定語 | 参照先 |
|--------|-------|
| MCP 連携モード | future-candidates（案 C）確定後に追加 |
| リアルタイム更新 | future-candidates 確定後に追加 |
| 統計ビュー | future-candidates 確定後に追加 |
| Step 完了履歴ビュー | Step 独立ビュー化（Q2=B の将来拡張）が承認された後に追加 |

> **削除済み**: 「個別実行ループ」は Q1=D（2026-06-20）で terminology.md の Task に統合。独立定義なし。

---

## 参照

- `.claude/rules/terminology.md`（用語階層の権威的定義。本ファイルと矛盾する場合は terminology.md が優先）
- `docs/specs/b4-dashboard/requirements.md`（b4-dashboard 要件定義書・未解決質問 Q1〜Q5）
- `.claude/rules/planning-quality-guideline.md`（PLANNING 品質基準）
- `SESSION_STATE.md` §5（骨子 ⑤「可視化レイヤー」）
