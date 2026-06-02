# インシデント記録: Claude Code ツール malformed 障害

- 記録日: 2026-06-02
- 記録者: Claude（LAM セッション）
- ステータス: 原因究明済み・回避策確立・本体は未修正バグ
- 関連: GitHub issue 番号 60033（open・本命） / issue 番号 8004（closed・連鎖の説明） / メモリ claude-code-malformed-write-bug / SESSION_STATE.md

## 概要

Claude Code のツール呼び出しが断続的に「malformed and could not be parsed」で失敗する現象。前セッション（whole-project 監査・CP-C 精査）の後半でこれが多発し、作業が中断していた。別セッションで調査し、既知の未修正バグと判明した。

## 環境

- OS: Windows 11
- Claude Code: 2.1.159（調査時点の latest。next は 2.1.160 が開発中）
- モデル: Claude Opus 4.8
- インストール形態: ネイティブ（npm グローバル管理の外）

## 症状

- Write / Edit などのツール呼び出しが「malformed and could not be parsed」のパース失敗で落ちる。
- 一度起きると同一セッション内で連鎖し、失敗が続く。
- 新セッション切替や再起動で回復する。
- 静的な設定や json とは無関係。

## 原因

GitHub issue 番号 60033（open・未修正）が本命。Write に渡す内容が大きく、かつエスケープ密度が高い場合に、ツール呼び出しの入力 JSON が壊れる。内容は JSON 文字列として送られるため、バックスラッシュの二重化・引用符・改行のエスケープが必要になり、長さとエスケープ密度に比例して不正なエスケープが混入しやすくなる。1 か所壊れると入力 JSON 全体がパース不能になる。Claude Code の自動リトライは同一の内容を再送するため同じく失敗する。バージョンは既に latest なのでアップデートでは直らない。

固定のサイズ上限ではない点が重要。短くてもエスケープが濃い文書は失敗し、長くても素直な文章は通る。真の変数は「1 回の呼び出しに載る内容の量 × エスケープ密度」である。

## 連鎖の機構（推定）

壊れたツール呼び出しブロックが会話履歴に残ると、後続のツール呼び出しと結果の整合が崩れる（issue 番号 8004 的な 400 連鎖）。これが「同一セッションで壊れ続ける」の正体と考えられる。新セッションでは履歴がリセットされるため回復する。

## 本セッションでの観測

- 調査セッション中にも実測で 2 回発生した。
- いずれも単発どまりで、連鎖には発展しなかった。
- 連鎖を避けられた理由は、失敗後に同一操作を機械的にリトライせず、操作を小さくする・Read を挟むなど戦略を変えたため。
- 逆に言えば、詰むのは Claude Code が同一の大きな内容を自動リトライして失敗を繰り返すとき。
- 本インシデント文書と SESSION_STATE への追記はすべて低密度の書き方で行い、malformed を 1 度も踏まずに完了した。これ自体が回避策の有効性の実証になっている。

## 対策

主対策（Claude 側の書き方）:

- 大きくエスケープ密度の高いファイルを一度の Write で書かない。
- 小さい Write で骨格を作り、Edit で追記する。または内容をチャンクに分割する。
- ドライブレターつきパス・正規表現・コードブロック・エスケープ例が濃い文書ほど分割する。
- バックスラッシュ区切りのパスはフォワードスラッシュや言語表現に置き換えて密度を下げる。

補完策（ファイル構造）:

- 全面書き換えや大規模編集の対象になる大きいファイルを物理分割しておくと、将来の書込内容が構造的に小さくなり確率が下がる。
- ただし読み込み専用のファイルは無関係（Read の入力は file_path のみ）。効くのは書込対象のファイル。
- プロジェクト本体への分割実行は次セッション以降（本セッションは本体不可侵の方針）。

## 回復手順

1. Esc を 2 回、または /rewind で、壊れる前のチェックポイントに巻き戻す（コンテキストを保ったまま連鎖を解消）。
2. 直らなければ新セッションに切り替える。

## GitHub 報告について

外部報告（issue 番号 60033 への投稿）は今回見送り。投稿する場合は本文書の「環境」「症状」「本セッションでの観測（Windows と Opus で同症状）」を抜粋・汎用化し、issue 番号 60033 のコメントに追記するとよい。既存 issue が詳細なため新規 issue は不要。

## 参考

- GitHub issue 番号 60033（本命・open）: Write の大きくエスケープ密度の高い内容で入力 JSON が壊れる。
- GitHub issue 番号 8004（closed）: ツール呼び出しと結果の整合崩れによる 400。連鎖の説明。
- GitHub issue 番号 63547（参考・別系統）: Windows で computer-use 系ツールが初回後に切断。
- メモリ: claude-code-malformed-write-bug。
- セッション状態: SESSION_STATE.md の「ツール malformed 障害 調査決着」。

---

## Update 2026-06-02（2.1.160 リリース後の再調査・主因再分類）

CC 2.1.160 リリースを受けた再裏取りで、当初分析を**根本的に修正**する必要が出た。要旨: **真の現主因は #60033 単体ではなく Opus 4.8 の tool_use 破損退行（2.1.150 導入）**。本記録の「対策」は #60033 系サブケースには有効だが、主クラスタはサイズ非依存のため**書込分割だけでは消えない**。

### 1. 2.1.160 でも未修正であることの確認

- CHANGELOG 全文走査（4146行・最新=2.1.160）。`could not be parsed` 文字列は**一度も出てこない**。
- 2.1.160 の 27 項目はすべて背景エージェント / Windows TUI / クリップボード・IME 系で、tool_use エンコーダに触れる項目はゼロ。
- Windows + heavy CPU load の入力不応答 fix は語感は近いが**キー入力→TUI の応答性**の話で、parse 失敗とは別クラス。
- 最有力の間接候補だった 2.1.156「Opus 4.8 の thinking ブロック改変を修正」も、出荷後に malformed 件数が**増加**しており実測で反証（#64176/#64235 が v2.1.158 で 68件・57件観測）。
- 「v2.1.116 で全解決」という検索結果は時系列矛盾（issue 報告日が 5–6月）・全件 OPEN・CHANGELOG 無記載の3点で却下。

### 2. 主因の再分類（#60033 → Opus 4.8 退行クラスタ）

| 観点 | 当初記録 | 再調査後 |
|---|---|---|
| 追跡 issue | #60033 単体 | **#60033 含む 12件以上の重複クラスタ** |
| 中核機構 | 大 Write の入力 JSON エスケープ破損 | **`stop_reason=tool_use` なのに content が thinking のみ・tool_use ブロック欠落**（#64235/#63481/#64418） |
| サイズ依存 | あり（大 Write で発生） | **なし**（単純な Bash でも発生 = #64235 area:bash） |
| ツール依存 | Write/Edit 中心 | **なし**（ツール非依存・退行ベースライン） |
| 導入バージョン | 不明 | **2.1.150**（#64176 の二分探索: 2.1.148 で 0件 → 2.1.150 で初発 → 2.1.152 で 19件 → 2.1.158 で 68件と単調悪化） |
| モデル相関 | 言及なし | **Opus 4.8 で頻発・Opus 4.7 では出ない**（#63604 で確認） |
| 本プロジェクト直撃 issue | #60033 | **#63687**（"Opus 4.8 (1M context) — frequent tool_use malformed client errors"・platform:windows・has repro） |

### 3. 関連 issue（全件 OPEN・2026-06-02 時点）

- **#60033**: Built-in Write tool: large escape-dense content intermittently yields malformed tool-input JSON; retry resends identical payload and also fails（Windows 11 / CC 2.1.143 / opus-4-7）— 本記録の原典。クラスタの1サブケース。
- **#63604**: Opus 4.8 repeatedly emits malformed tool_use blocks, entire response discarded (4.7 works fine)— **4.7 切替で解消**を確認した重要 issue。
- **#63687**: Opus 4.8 (1M context) — frequent "tool_use malformed" client errors despite tools executing successfully（platform:windows）— **本プロジェクトのモデルに直接該当**。
- **#64176**: Regression in 2.1.150-2.1.158: malformed tool_use blocks not parseable, retry-resistant — **退行の二分探索**を行った決定的 issue。
- **#64235**: Regression (since 2026-05-29): intermittent "tool call was malformed and could not be parsed"（area:bash, platform:macos）— **単純な Bash でも発生**を示す根拠。
- **#64127**: Spurious "tool call was malformed and could not be parsed" appended after successful tool calls（platform:windows）。
- **#63481**: Tool call parsing fails when extended thinking is triggered（platform:macos）。
- **#64418**: Tool calls serialized as plain text instead of tool_use blocks in high-composition sessions（platform:macos, has repro）。
- **#64658**: Desktop app (Code tab) 1.9659.4: Opus 4.8 "tool call could not be parsed"（area:desktop, platform:macos）。
- **#61133（CLOSED）**: Opus 4.7 tool calls fail... since 2026-05-20（CC 2.1.146, opus-4-7）— 文言は類似だが**別系統**（サーバ側モデル退行・修正版明記なし）。

### 4. 対策の優先順位（更新版）

1. **根本回避（最優先）: モデルを Opus 4.7 (1M context) へ切替** — `/model claude-opus-4-7[1m]`。本プロジェクトでは 2026-06-02 にこの対応を採用。Auto Mode + 4.7 で再開可能。
2. **代替の根本回避: CC 2.1.149 へダウングレード** — #64176 の二分探索で「退行前」と確認されたバージョン。
3. **4.8 のまま続ける場合の緩和**: 既存対策（大 Write 分割）は #60033 系サブケースには有効。ただし**主クラスタはサイズ非依存なので分割だけでは消えない**。
4. **コンテキスト総量を抑える**: コミット境界で `/quick-save` → 新セッション。長セッションほど確率が上がる（本セッションの実観測でも、後半に密度の低い Bash でも malformed が発生）。

### 5. 本記録の前提のうち陳腐化したもの

- 「バージョンは既に latest（2.1.159）なのでアップデートでは直らない」→ 2.1.160 が出たので前提は古い。ただし 2.1.160 にも修正がないため**結論（未修正）は不変**。
- 「Write の大きくエスケープ密度の高い内容で入力 JSON が壊れる」→ #60033 サブケースとしては正しい。だが**全体の主因ではない**。

### 6. 裏取りのトレース

- CHANGELOG: https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md（4146行全走査）
- 主要 issue を WebFetch で直接確認（#60033 / #63604 / #61133 / 一覧）
- 敵対的検証（反証試行）で「未修正」結論を強化（refutesNotFixed=false / confidence=high）

### 7. 関連メモリ

`claude-code-malformed-write-bug.md` も同日に更新（同じ再分類）。
