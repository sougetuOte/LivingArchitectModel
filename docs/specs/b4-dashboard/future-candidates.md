# b4-dashboard — 将来候補リスト

作成日: 2026-06-20
根拠: `docs/specs/b4-dashboard/requirements.md` §9 / `docs/specs/b4-dashboard/design.md` §10・§13
ステータス: 設計フェーズ確定後の記録

本ファイルは b4-dashboard（B-5）の現スコープから除外された候補を記録する。
各候補には起源・採用トリガ・不採用理由・再評価時のチェック項目を明記する。

---

## FC-1: 複数 Project 対応

- **起源**: Q3=B（V-1 を LAM 単一プロジェクト固定のトップサマリーページとして確定）採用時の将来想定（requirements.md §8 Q3・FR-1 注記）
- **内容**: V-1 に Project 切り替えタブを追加し、複数の独立した Project（LAM 以外のプロジェクト）を同一ダッシュボードで切り替えて表示する
- **不採用理由**: 現時点では LAM 単一プロジェクト固定であり、複数 Project の管理ニーズが発生していない。V-1 をトップサマリーページとして設計することで、将来の拡張時に設計変更なしにタブ追加で対応可能な構成を維持している
- **採用トリガ**: LAM 以外の 2 つ目のプロジェクトをダッシュボードで管理する必要が生じた時点
- **再評価時のチェック項目**:
  - V-1 のタブ UI 追加コスト（HTML テンプレートの修正範囲）
  - FR-4 データソース（SESSION_STATE.md 等）の Project 別パス管理ルール追加
  - CurrentPhaseParser が複数 Project のフェーズを独立して管理できるか（`current-phase.md` の Project 別分割要否）
  - NFR-1（500KB 未満）への影響（複数 Project 分のデータ増加）

---

## FC-2: Step 完了履歴の独立ビュー化

- **起源**: Q2=B（Step を V-2 の属性列として表示・独立ビューなし）採用時の将来想定（requirements.md §8 Q2・FR-1 注記）
- **内容**: V-2.5 として Step 完了履歴ビューを独立させ、Milestone ごとに PLANNING → BUILDING → AUDITING の承認ゲート通過状況を時系列で一覧できるようにする
- **不採用理由**: 現時点は「現在の Step が何か」を知ることが主要ニーズであり、Step の時系列履歴に対するニーズが確認されていない。V-2 の属性列として現在 Step を表示するだけで十分
- **採用トリガ**: Milestone が複数並行進行するようになり、各 Milestone の Step 遷移履歴（いつ PLANNING から BUILDING に移行したか等）を時系列で追跡したいニーズが生じた時点
- **再評価時のチェック項目**:
  - Step 遷移履歴のデータソース（git log のコミットメッセージから抽出可能か / `.claude/current-phase.md` では履歴が保持されない）
  - GitHistoryParser の拡張コスト（Phase 移行コミットのパターン定義）
  - V-2.5 の DOM 設計（V-2 のサブセクションとして展開するか、独立 `<section>` とするか）

---

## FC-3: 個別実行ループ概念の再評価

- **起源**: Q1=D（「個別実行ループ」を terminology.md の Task に統合・独立ビューなし）の将来拡張可能性（requirements.md §8 Q1・design.md §2 Non-Goals）
- **内容**: TDD サイクル / セッション粒度のデータが安定して記録される運用が確立した段階で、「個別実行ループ」または同等概念を独立したビュー（V-5 相当）として再評価する。当初検討の候補 A（SESSION_STATE.md §5「5 階層モデル」の独立ビュー）〜C のどれかに相当する形での再採用を想定する
- **不採用理由**: 「個別実行ループ」は terminology.md の Task に統合済みであり、現スコープでの独立定義はモデルの一貫性を損なう。また TDD サイクル粒度のデータを構造化して記録する運用が確立していないため、データソースが存在しない
- **採用トリガ**: TDD サイクル単位またはセッション単位の実行記録が `.claude/` 配下の構造化ファイルに安定して蓄積される運用が確立し、それを可視化したいニーズが生じた時点
- **再評価時のチェック項目**:
  - 「個別実行ループ」相当の記録ファイル（データソース）の存在と形式
  - terminology.md でのモデル再定義の要否（Task との関係整理）
  - V-4（Task 一覧）との重複・差別化

---

## FC-4: 案 C — MCP 連携（B → C ハイブリッド）

- **起源**: design.md §10 Alternatives Considered 案 C・requirements.md §2 Non-Goals・§9 将来候補
- **内容**: `build_dashboard.py` のパーサ層を MCP サーバーのエンドポイントとして公開し、ダッシュボード HTML をクライアントサイドで MCP API 経由のリアルタイムデータ取得に移行する。Phase 1（B-5）の B 案実装後の Phase 2 拡張として位置付ける

  ```
  B → C ハイブリッド拡張の方針:
    Phase 1（B-5）: 単一 HTML 生成スクリプト（案 B）を実装
    Phase 2（将来）: パーサ層を MCP サーバーのエンドポイントとして公開
                     HTML はクライアントサイドで MCP API を呼ぶ形式に移行
  ```

- **不採用理由**: MCP サーバーの常駐が必要であり、Windows 環境でのプロセス管理コストが高い。実装コストが案 B の数倍に達する。ブラウザからの参照に追加の HTTP アダプタ層が必要。`.claude/settings.json` への MCP サーバー設定追加（PM 級変更）が発生する。FR-5（外部サービス依存なし・オフライン動作）と部分的に矛盾する
- **採用トリガ**: 案 B（単一 HTML 生成）が安定稼働し、かつ他のエージェント / ツールからプログラム的にダッシュボードデータを参照したいニーズが具体化した時点
- **再評価時のチェック項目**:
  - MCP サーバー実装コスト（パーサ層の MCP エンドポイント化に必要な工数）
  - Windows 環境での常駐プロセス管理方法（`settings.json` の `mcpServers` 設定）
  - ブラウザ ↔ MCP サーバー間の HTTP アダプタ設計
  - FR-5（オフライン動作）の部分的な緩和要否と PM 承認
  - upstream 裏取り: MCP サーバーの Claude Code 公式書式（`settings.json` の `mcpServers` キー名・フロントマター等）は実装前に context7 / 公式ドキュメントで確認すること（planning-quality-guideline.md §7 段階1）

---

## FC-5: 配色・UI スタイリングの確定

- **起源**: design.md §2 Non-Goals（「具体的な CSS スタイリング・配色設計: 最小限の inline style のみ。UI デザインは PoC 後のフェーズで決める」）・design.md §8 注記（配色値は構造例示のための仮置き）
- **内容**: PoC 版で仮置きした配色（`#28a745` / `#007bff` 等）を確定し、ブランドカラー・アクセシビリティ基準（WCAG AA 以上）・ダークモード対応等を含む正式な UI スタイリング仕様を策定する
- **不採用理由**: B-5 の主目的はデータ可視化機能の実現であり、スタイリング確定は二次的な関心事。PoC 完了前に配色を確定しても、ビュー構成変更に伴うやり直しリスクが高い
- **採用トリガ**: BUILDING フェーズで PoC 実装が完了し、ビュー構成（V-1〜V-4）が安定した後に UI 設計フェーズとして着手する
- **再評価時のチェック項目**:
  - WCAG 2.1 AA 適合（コントラスト比 4.5:1 以上）の確認ツール選定
  - LAM プロジェクトのブランドカラー定義の有無
  - ダークモード対応要否（`@media (prefers-color-scheme: dark)` の採用判断）
  - CSS カスタムプロパティへの移行（現行の仮置き inline style を変数化）

---

## FC-6: 多言語化（i18n）

- **起源**: design.md §2 Non-Goals / requirements.md §2 Non-Goals
- **内容**: UI ラベル・状態値の表示テキスト・エラーメッセージを多言語対応（最低限: 日英切り替え）とする
- **不採用理由**: LAM プロジェクトは現時点で日本語単一環境での利用を前提としており、国際展開ニーズが存在しない
- **採用トリガ**: LAM プロジェクトを英語圏または多言語環境で利用するニーズが具体化した時点
- **再評価時のチェック項目**:
  - i18n ライブラリの選定（素 JS での辞書オブジェクト方式 vs 外部ライブラリ）
  - NFR-1（500KB 未満）への影響（辞書データの追加分）
  - FR-5（外部依存なし）との整合（i18n ライブラリを inline 埋め込みできるか）
  - glossary-draft.md の英語版対応要否

---

## FC-7: 複数 Milestone 同時進行時の Step 表示方針

- **起源**: design.md §13 UQ-7 相当（複数 Milestone 並列進行時の CurrentPhase 管理）・design.md §4 V-2 注記
- **内容**: 複数の Milestone が並列進行する場合に、各 Milestone の Step（PLANNING / BUILDING / AUDITING）を独立して管理・表示する。現行設計では `.claude/current-phase.md` が単一フェーズ文字列を返すため、全 Milestone に同一の Step が表示される

  > 現行設計からの引用（design.md §4 V-2 注記）: 「複数 Milestone が存在する場合は全 Milestone に同じ Step を表示する（現時点は LAM 単一プロジェクト固定）。Step の Milestone 別管理は将来候補（将来複数 Step が必要になった段階で再設計）。」

- **不採用理由**: 現時点では実質的に 1 Milestone ずつ進行しており、Milestone 別フェーズ管理の設計コストをかける優先度が低い。単一フェーズファイル（`.claude/current-phase.md`）で十分
- **採用トリガ**: 2 つ以上の Milestone が同時に BUILDING・AUDITING 等の異なる Step で並列進行する状況が常態化した時点
- **再評価時のチェック項目**:
  - `current-phase.md` の Milestone 別分割方式（例: `.claude/phase-B-5.md` / `.claude/phase-B-6.md`）またはフロントマター形式への変更
  - CurrentPhaseParser の拡張（Milestone 名を引数として受け取る設計変更）
  - terminology.md・glossary-draft.md の更新要否（Phase の定義を Milestone スコープに限定する場合）
  - current-phase.md フォーマット変更は SE 級変更として取り扱えるか（permission-levels.md 確認）

---

## FC-8: 統計可視化（バーンダウン / 進捗率推移）

- **起源**: requirements.md §2 Non-Goals（「グラフ・チャートによる統計可視化（進捗率推移・バーンダウン等）: 将来候補」）・requirements.md §9 将来候補
- **内容**: Wave / Task の完了率推移をバーンダウンチャートや折れ線グラフで表示する統計ビューを追加する
- **不採用理由**: 現スコープでは「現在の状態（何が完了/進行中/未着手）」の把握が主目的であり、時系列統計は二次的ニーズ。また時系列データの蓄積には履歴記録の仕組みが別途必要となり、本スコープの「既存ファイルをデータソースとして活用する」方針と整合しない
- **採用トリガ**: ダッシュボードの基本ビュー（V-1〜V-4）が安定稼働し、かつ作業速度・完了率の時系列トレンド把握ニーズが生じた時点
- **再評価時のチェック項目**:
  - 時系列データの蓄積方式（git log からの差分抽出 / ダッシュボード生成時のスナップショット記録）
  - NFR-1（500KB 未満）への影響（チャートライブラリのサイズ）
  - チャートライブラリの選定と FR-5（外部依存なし）との整合（inline 埋め込みの可否）
  - Chart.js（~200KB）/ D3.js（~100KB）等の候補評価

---

## FC-9: リアルタイム更新（ファイル監視）

- **起源**: requirements.md §2 Non-Goals（「リアルタイムでの自動更新（更新間隔・プッシュ通知等）: Q4 で確定後に設計フェーズで判断」→ Q4=B で `/quick-save` 連動として解決済み）・requirements.md §9 将来候補
- **内容**: `watchdog` 等のファイル監視ライブラリを用いて、データソースファイル（SESSION_STATE.md 等）の変更を検知し、ダッシュボード HTML をブラウザのリロードなしに自動更新する
- **不採用理由**: `/quick-save` 連動（Q4=B）で「必要な時点での更新」は実現されている。常時ファイル監視はプロセス常駐コストとバッテリー消費を伴い、Windows 環境での安定動作に懸念がある。NFR-4（生成 30 秒以内）の上乗せ問題も未解決
- **採用トリガ**: `/quick-save` 連動による更新では頻度が不足し、SESSION_STATE.md 変更をリアルタイムで反映したいニーズが生じた時点
- **再評価時のチェック項目**:
  - `watchdog` ライブラリの Windows 環境での動作確認
  - NFR-5（標準ライブラリのみ / pyproject.toml 管理）との整合
  - ブラウザのライブリロード方式（WebSocket / Server-Sent Events / ポーリング）の選定
  - プロセス常駐の管理方法（起動・停止・クラッシュ時の挙動）

---

## FC-10: `/project-vision` スキル連携

- **起源**: requirements.md §9 将来候補（「`/project-vision` スキル連携（⑥）: プロジェクト俯瞰オーケストレータとのデータ連携（⑥ の設計確定後）」）
- **内容**: LAM 骨子 ⑥「プロジェクト俯瞰オーケストレータ」（`/project-vision` スキル候補）が確立した後、ダッシュボードとのデータ連携を実装する。ダッシュボードが `/project-vision` の出力データをデータソースとして取り込む、またはその逆方向の連携を検討する
- **不採用理由**: ⑥「プロジェクト俯瞰オーケストレータ」の設計が未確定であり、連携仕様を定義できる段階にない
- **採用トリガ**: LAM 骨子 ⑥（`/project-vision` または同等スキル）の設計が確定し、ダッシュボードとの連携設計が可能になった時点
- **再評価時のチェック項目**:
  - `/project-vision` が生成するデータ形式・ファイルパス
  - b4-dashboard データソース（FR-4）への追加要否と設計変更範囲
  - データ連携方向（一方向 / 双方向）の設計判断

---

## 参照

- `docs/specs/b4-dashboard/requirements.md`（§2 Non-Goals / §8 解決済み質問 / §9 将来候補）
- `docs/specs/b4-dashboard/design.md`（§2 Non-Goals / §10 Alternatives Considered / §13 未解決設計事項）
- `docs/specs/b4-dashboard/glossary-draft.md`（§6 将来候補語）
- `.claude/rules/terminology.md`（用語階層の権威的定義）
- `.claude/rules/planning-quality-guideline.md`（§7 新機能・外部依存の採用評価）
- `docs/specs/v5-fat-reduction/future-candidates.md`（章構成の参考）
