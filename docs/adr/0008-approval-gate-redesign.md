# ADR-0008: 承認ゲート再設計 — 自己責任モデル + AutoMode 提案 + 最小核 LAM 規律

## メタ情報

| 項目 | 内容 |
|------|------|
| ステータス | **Accepted**（2026-06-30 起草・即日 PM 一括承認 / sougetuOte） |
| 日付 | 2026-06-30 |
| 意思決定者 | sougetuOte（最終承認）/ Living Architect（起草・MAGI 合議） |
| 関連 ADR | [ADR-0005](./0005-thin-harness-autonomous-governance.md)（薄ハーネス / 自治）, [ADR-0006](./0006-loop-engineering-vocabulary-and-lam-alignment.md)（Loop Engineering 語彙）, [ADR-0007](./0007-magi-v2-gabriel-integration.md)（gabriel 統合） |
| 関連仕様 | （本 ADR 採用後に作成予定）`docs/specs/approval-gate-v2/compatibility-matrix.md`（CC バージョン × `defaultMode` 配置可否） |
| 関連資産 | `.claude/rules/permission-levels.md`, `.claude/rules/security-commands.md`, `.claude/hooks/pre-tool-use.py`, `.claude/hooks/post-tool-use.py`, `CLAUDE.md`, `docs/internal/07_SECURITY_AND_AUTOMATION.md`, `docs/artifacts/B5-future-considerations-2026-06-30.md`, memory `lam-hook-overlap-removal-plan`, memory `settings-json-edit-blocked` |

---

## コンテキスト

### 背景: 承認ゲート 70% 形骸化 + AutoMode 登場

ユーザー体感: 承認の約 **70% が定型動作**（設定ファイル書き込み・PyTest 実行 等）で「めんどくさい」体感が増加。残り 30% の重要判断にも注意力が分配されて薄まり、形だけのレビューと同じ構造で **承認ゲートが残っているのに機能していない最悪の状態に近づいている**。

Anthropic 公式: auto mode 発表記事で **「93% 承認」「developer is playing approve-bot rather than doing actual work」** と内部問題を認知。ユーザー体感は公式実測と整合。

Claude Code 側の新機能: v2.1.83+ で **AutoMode**（`permissions.defaultMode = "auto"`）導入。Sonnet 4.6 classifier + soft_deny 一覧 + circuit breaker の三層防御で承認 prompt を background safety check に置換。

LAM が独自に PG/SE/PM 三層 + `permissions.allow` 拡大で形骸化解消を目指すアプローチは、AutoMode との二重化リスクを抱える。

### 上流調査の主要発見（2026-06-30）

| # | 発見 | 出典 |
|---|------|------|
| 1 | `permissions.defaultMode` は v2.1.142+ で `.claude/settings.json` / `.claude/settings.local.json` 配置時は無視（self-grant 防止）。`~/.claude/settings.json` または managed settings のみ有効 | code.claude.com/docs/en/permissions, agent-sdk/permissions |
| 2 | AutoMode 三層防御: classifier 評価 + soft_deny（`git push --force`, `git reset --hard`, `terraform destroy`, `curl \| bash` 等）+ circuit breaker（`rm -rf /`, `rm -rf ~` は全モードで強制 prompt） | claude.com/blog/auto-mode, code.claude.com/docs/en/permission-modes |
| 3 | PreToolUse hook の `deny` は AutoMode を含む全モードを上書きする（deny-first 維持） | code.claude.com/docs/en/agent-sdk/hooks |
| 4 | 広汎 allow（`Bash(*)` 等）は auto 進入時に drop / narrow rule のみ残存 | code.claude.com/docs/en/auto-mode-config |
| 5 | CC 側未解決バグ: ワイルドカード `Bash(*)` / `Edit(*)` / MCP `mcp__*` 未尊重（GH #27139 / #9924 Critical / #13077） | github.com/anthropics/claude-code/issues/* |
| 6 | 事故事例: Reddit Mac home wipe（`rm -rf ~/` 展開）/ Claude Cowork 11GB 削除 / `.docx` 白文字 prompt injection 漏出 | webpronews / thomas-wiegold blog / Simon Willison |
| 7 | 競合: Cline = step-level / 最 auditable / Cursor denylist は 1.3 で廃止（Base64 obfuscation で bypass） / Aider = 最小 ask だがガードレールも最少 | backslash.security / cline GitHub |
| 8 | LangGraph `interrupt()` の resume payload は approve / **edit** / reject / respond の 4 値（edit で修正値返し可能） | docs.langchain.com/oss/python/langchain/human-in-the-loop |

### 問題

1. **形骸化した承認は判断品質を下げる方向に作用** している（30% 重要判断の注意力が薄まる / Anthropic 公式が approve-bot 問題を認知）
2. **LAM 側から AutoMode を強制できない**（`.claude/settings.json` の `defaultMode` は v2.1.142+ で無視）
3. **広汎 allow と CC 側ワイルドカード未尊重バグにより allowlist 設計が脆い**（GH #27139 / #9924 / #13077）
4. **AutoMode に頼り切ると LAM 固有規律（PM 級 / インシデント履歴 / AUTONOMOUS 統治）が失われる**
5. **アンチパターン警戒**: Cursor denylist 単独廃止 / YOLO スイッチ事故 / OpenHands sandbox 全許可境界の脆さを反面教師として組み込む必要

### 制約条件

- ユーザー判断（2026-06-30）: LAM は強制せず **認知 + 提案 + 文書化に倒す自己責任モデル**
- ユーザー判断（2026-06-30）: 不可逆 hook 重ね掛けは **当面残す / 将来撤去**（memory `lam-hook-overlap-removal-plan`）
- LAM **Hierarchy of Truth: User Intent が最上位** → 自己責任モデルと整合
- **upstream-first**: AutoMode 仕様変更への追従義務（Phase B で互換性表新設）
- 権限等級: **PM 級**（`.claude/rules/permission-levels.md`, アーキテクチャ変更 + 新 ADR）

---

## 検討した選択肢

### 案 1: 却下 — 承認ゲートを廃止

**概要**: 承認ゲートを全廃し AutoMode に丸投げ。

**却下理由**:
- PM 級ファイル / インシデント履歴 / AUTONOMOUS 統治は LAM 固有規律であり AutoMode に対応物なし
- 完全廃止は LAM の存在意義（人間の制御権を保つフレームワーク）を消す
- Aider `--yes-always` / Cline YOLO の事故事例（反面教師 D2）を再現するリスク

### 案 2: 却下 — `permissions.allow` 拡大で形骸化吸収（前ターン MAGI 合議 A2 結論）

**概要**: SE 級 × reversible_internal の典型パターンを `.claude/settings.json` `permissions.allow` に追加し、形骸化 70% を自動 allow 化。

**却下理由**:
- AutoMode 進入時に広汎 allow は drop（上流発見 4）
- `.claude/settings.json` の `defaultMode` は無視（上流発見 1）→ ユーザー環境次第で挙動が不安定
- CC 側ワイルドカード未尊重バグ（GH #27139 / #9924）で実装が脆い

### 案 3: 却下 — LAM 側で AutoMode を強制

**概要**: `init-harness` 等で `~/.claude/settings.json` を書き換え `defaultMode: "auto"` を強制。

**却下理由**:
- PM 級ファイルかつ LAM に書き資格なし（ユーザー領域ファイル）
- ユーザー設定への侵襲は memory `settings-json-edit-blocked` 方針と矛盾
- 強制は LAM の Hierarchy of Truth（User Intent 最上位）に反する

### 案 4: 採用 — 自己責任モデル + AutoMode 提案 + 最小核 LAM 規律

**概要**: LAM は AutoMode を強制せず、**認知 → 提案 → 文書化** に倒す。LAM 規律は両前提（AutoMode 採用/非採用）共通の最小核（PM 級 / インシデント履歴 / AUTONOMOUS 統治）+ 暫定的な不可逆/外部送信重ね掛けに絞る。

**採用理由**:
- User Intent 最上位 + 自己責任モデル（ユーザー判断 2026-06-30 と整合）
- AutoMode の三層防御を信頼 + 反面教師制約（D1-D4）で二重化リスク回避
- 段階移行 Phase A/B/C（前ターン MAGI の 3 Phase から 2 Phase + 将来判断ゲートに縮小）で実装可能
- Phase C 末で重ね掛け撤去 3 条件達成時に設計純化

---

## 決定

採用案 4 を以下 6 軸 + 段階移行で実装する。

### 軸 1: モード認知の技術的実装（B1）

- **一次手段**: `/quick-load` skill および `init-harness` skill で `~/.claude/settings.json` を Read し `permissions.defaultMode` を抽出
- **二次手段**: 一次失敗時は managed settings の典型パス（POSIX: `/etc/claude-code/managed-settings.json` / Windows: `%PROGRAMDATA%/ClaudeCode/managed-settings.json`）を Read 試行（権限なければスキップ + warning ログ）
- **available チェック**（Reflection R2 反映）: CC バージョン（v2.1.83+ 要件）+ 3rd-party モデルの場合 `env.CLAUDE_CODE_ENABLE_AUTO_MODE=1` の検知も併せ、available 確認後に推奨表示
- **失敗時**: 「認知不能」を `/quick-load` 出力末尾に明示 → 軸 3 の文書化に依存
- **実装**: 共通ヘルパー `.claude/scripts/detect-permission-mode.py`（新規 / SE 級）に切り出し `/quick-load` + `init-harness` から共有

### 軸 2: 認知時のユーザー提案 UX（B2）

> **追記 (v0.3 / 2026-06-30 同日)**: 本軸の **自動実行部分**（`/quick-load` 1 行サマリ自動表示 + `init-harness` 初回比較表自動表示）は Phase A 実装当日の運用で **承認 prompt ノイズ過大** が判明し、**同日内に撤回** した。`.claude/scripts/detect-permission-mode.py` 本体は debug / ユーザー手動実行用として温存。Advisory 認知は **軸 3**（`CLAUDE.md` 冒頭 Advisory + `07_SECURITY_AND_AUTOMATION.md` § AutoMode Advisory + `security-commands.md` 反面教師制約）で代替する。本セクション本文は当初決定の記録として保持。詳細は改訂履歴 v0.3 参照。

- **`/quick-load` 出力末尾 1 行サマリ** — `defaultMode` 値別に分岐:

  | mode | 出力 |
  |---|---|
  | `"auto"` | `Mode: auto (LAM 推奨設定 / Claude 自律性最大)` |
  | `"default"` / `"acceptEdits"` / `"plan"` / `"dontAsk"` | `Mode: <値> (AutoMode 採用を推奨 / 詳細: CLAUDE.md §Permission Modes Advisory)` |
  | `"bypassPermissions"` | `Mode: bypassPermissions ⚠ AutoMode への切替を強く推奨 (LAM 規律 hook のみ稼働中)` |
  | 検知不能 | `Mode: 不明 (~/.claude/settings.json 読み取り失敗 / 詳細: CLAUDE.md §Permission Modes Advisory)` |

- **`init-harness` 初回 1 度限り比較表** — 3 モード（default / auto / bypassPermissions）の比較表 + 採用手順（`~/.claude/settings.json` への手書き手順）を提示
- **フラグ管理**: `.claude/harness.json` に `auto_mode_advisory_shown: <ISO timestamp>` を記録 / 2 回目以降スキップ
- **フラグ破損時挙動**（Reflection R1 反映）: ISO timestamp 形式不正 or キー欠落の場合は「初回扱い」（再表示）+ warning ログ
- **LAM 側書き換えゼロ原則**: `~/.claude/settings.json` の書き換えは LAM から絶対にしない（PM 級 + 書き資格なし）/ ユーザー手書き手順のみ提示

### 軸 3: 認知不能時の文書化方針（B3）

- **`CLAUDE.md` 冒頭**（`## Identity` 直後 / `## Hierarchy of Truth` 直前）に `## Execution Permission Modes (Advisory)` セクションを 5-10 行で新設
- **表記**: RFC 2119 **SHOULD**（"LAM utilization SHOULD set `permissions.defaultMode = "auto"` in `~/.claude/settings.json`"）。**MUST は使わない**（LAM は強制しない方針 / 建前と挙動の食い違いを避け形骸化の再現を防ぐ）
- **詳細**: `docs/internal/07_SECURITY_AND_AUTOMATION.md` 末尾に `§ AutoMode Advisory` セクション追記（soft_deny 一覧 + circuit breaker 挙動 + LAM 規律との関係 + Phase C 末撤去計画）
- **専用文書は新設しない**（07 で吸収 / 文書増殖回避）
- **`.claude/rules/permission-levels.md` は変更しない**（権限等級と AutoMode は別軸）

### 軸 4: LAM 規律として残す核（B4）

LAM 規律として残す核 = **C1 + C2 + C3（永続）+ C4（暫定）+ C5 + C6（TODO）**:

| # | 領域 | 実装場所 | 不変性 |
|---|---|---|---|
| **C1** | PM 級ファイル初回編集 ask + 2 回目降格 | `pre-tool-use.py` + `.session-pm-edit-cache.json`（既存） | **永続** |
| **C2** | インシデント履歴ベース動的 deny | `pre-tool-use.py` + `docs/artifacts/incident-patterns.yaml`（新規 / Phase B） | **永続** |
| **C3** | AUTONOMOUS フェーズ統治ファイル不可侵 | `pre-tool-use.py` FR-9 / FR-3.4（既存） | **永続** |
| **C4** | 不可逆 + 外部送信 hook 重ね掛け | `pre-tool-use.py`（既存） | **暫定 / Phase C 末で撤去判定** |
| **C5** | subagent 起動時の権限境界 | `pre-tool-use.py`（新規 / Phase B）| 永続 |
| **C6** | hook 障害時 fallback プロトコル | upstream 確認後 / TODO | 未定 |

### 軸 5: 反面教師制約の組み込み（B5）

ADR 採用と同時に LAM 設計の「やってはいけない事リスト」として明文化:

| # | 制約 | 根拠 | 適用箇所 |
|---|------|------|---------|
| **D1** | `.claude/rules/security-commands.md` の deny list は allowlist（PG 級 auto allow）と二重化必須 / deny 単独で守らない | Cursor denylist 単独廃止（Base64 obfuscation で bypass） | Phase A: `security-commands.md` 書き換え |
| **D2** | `permissions.defaultMode = "bypassPermissions"` 検知時の `/quick-load` 強警告 | Aider `--yes-always` / Cline YOLO 事故 | 軸 2 で実装済 |
| **D3** | サンドボックス境界を承認免除根拠にしない（in-sandbox でも PM 級は承認必須） | OpenHands sandbox 全許可（Docker socket mount 等の境界の脆さ） | 将来要件 / 本 ADR で明文化のみ |
| **D4** | LAM の allowlist 設計はワイルドカード非依存 / 明示コマンド列挙ベース | CC 側 GH #27139 / #9924 / #13077（ワイルドカード未尊重バグ） | Phase A: `permissions.allow` 設計 |

### 軸 6: 自己責任モデルの境界（B6）

- **重ね掛け維持**（C4 / ユーザー判断 2026-06-30）: 不可逆 + 外部送信の LAM hook 重ね掛けは当面残す。memory `lam-hook-overlap-removal-plan` 参照
- **重ね掛け撤去 3 条件**（Phase C 末判断ゲート）:
  1. AutoMode 採用率の観察: LAM ユーザーの大半が `defaultMode: "auto"` 採用
  2. 過去 90 日にインシデントなし（`docs/artifacts/incident-*.md` 起票なし）
  3. AutoMode soft_deny 一覧の完全性確認（upstream 直近変更がカバー範囲を狭めていないか）
- **edit-on-approve スコープ外**: LangGraph 風 4 値（approve / edit / reject / respond）は CC ネイティブ PreToolUse hook 返答仕様未確認 / `Future considerations` に記録のみ
- **自己責任モデル と PM 級事前宣言義務は両立**: PM 級事前宣言（core-identity.md / 2026-06-29）は「LAM の中の規律」（エージェント自身への自制）/ 自己責任モデルは「LAM がユーザーに対して強制しない」原則 / ベクトルが異なり対立しない

---

## 段階移行（Phase A / Phase B / Phase C 末）

### Phase A — 即時実装可能（SE-PG 級主体）

| Task | 種別 | 詳細 |
|------|------|------|
| A-1 | SE | `.claude/scripts/detect-permission-mode.py` 新規（軸 1 共通ヘルパー） |
| A-2 | SE | `/quick-load` skill 改修（軸 2 / 1 行サマリ + フラグ参照） |
| A-3 | SE | `init-harness` skill 改修（軸 2 / 初回比較表 + フラグ記録 + 破損時再表示） |
| A-4 | PM | `CLAUDE.md` 冒頭に `## Execution Permission Modes (Advisory)` 追加（軸 3） |
| A-5 | PM | `docs/internal/07_SECURITY_AND_AUTOMATION.md` 末尾に `§ AutoMode Advisory` 追記（軸 3） |
| A-6 | PM | `.claude/rules/security-commands.md` 書き換え（軸 5 / D1 deny ↔ allow 二重化 / D4 ワイルドカード非依存） |

### Phase B — 中期実装（PM 級主体 + upstream 追従）

| Task | 種別 | 詳細 |
|------|------|------|
| B-1 | PM | `docs/artifacts/incident-patterns.yaml` 新規（軸 4 C2 / 機械可読インシデントレジストリ仕様策定） |
| B-2 | SE | `pre-tool-use.py` 改修（軸 4 C2 / 動的 deny 実装 + C5 subagent 起動境界判定 + C2 の検知ログ） |
| B-3 | PM | `docs/specs/approval-gate-v2/compatibility-matrix.md` 新規（Reflection R4 / CC バージョン × `defaultMode` 配置可否表 / upstream 追従文書） |
| B-4 | SE | C2 のテスト（`.claude/tests/dashboard/test_incident_patterns_match.py` 等 / 既存テスト体系に合わせる） |

### Phase C 末 — 将来判断ゲート（重ね掛け撤去）

| Task | 種別 | 詳細 |
|------|------|------|
| C-1 | PM | 重ね掛け撤去 3 条件のチェック（軸 6 / B-5 retro 以降の Wave で実施） |
| C-2 | PM | C4 撤去判定（3 条件全達成時のみ / `pre-tool-use.py` から不可逆 + 外部送信 deny を削除） |
| C-3 | SE | 撤去後の回帰テスト（AutoMode soft_deny 経由で同等カバレッジが確保できているか確認） |

### スコープ外（Future considerations）

- C-6: LAM hook 障害時 fallback プロトコル（upstream 確認後）
- edit-on-approve 採用判断（CC ネイティブ仕様調査後）

---

## 結果（Consequences）

### Positive

- **形骸化解消**: CC AutoMode に多くを任せ、LAM は「人間の制御権を保つフレームワーク」として固有規律に集中
- **LAM 固有規律の明示化**: 永続核 C1 / C2 / C3 が ADR で文書化され「LAM 何のために残っているのか」が明確化
- **ユーザー責任の明確化**: 自己責任モデルにより LAM は強制しないことが SSOT で確定
- **実装工数削減**: 3 Phase → 2 Phase + 将来判断ゲートに縮小（前ターン MAGI 合議 A2 案比）
- **反面教師制約の明文化**: D1-D4 が将来の設計判断のガードレールとして機能

### Negative

- **AutoMode 未採用ユーザーは LAM 規律 hook のみで防衛**（一部リスク残存 / 但し軸 2 で強警告 / D2）
- **`init-harness` フラグ管理の追加複雑性**（Reflection R1 で再表示プロトコルを定義済）
- **CC バージョン追従の継続コスト**: `compatibility-matrix.md` のメンテ義務（Phase B-3 / upstream-first 原則の運用負荷）
- **重ね掛け撤去判定の不確実性**: 3 条件のうち「採用率の観察」は LAM 単独では測定困難 → ユーザーヒアリングまたは別途調査が必要

### Neutral

- **既存 PM 級事前宣言義務（core-identity.md / 2026-06-29）は変更なし**（自己責任モデルと両立 / 軸 6）
- **既存 `incident-*.md` ファイル**は形式変更なし（`incident-patterns.yaml` は新形式 / 既存は参照のみ）
- **`.claude/rules/permission-levels.md` PG/SE/PM 三層は維持**（AutoMode の軸とは別 / 軸 3）

---

## Future considerations

### 未確認事項（B-5 retro で再裏取り）

| # | 項目 | 状況 |
|---|------|------|
| **R3** | subagent 起動時の AutoMode 継承 / `permission_mode` 上書き可否 | Agent 4 報告で classifier 事前評価（v2.1.172）の存在は確認、上書き挙動は未確認 |
| **R4** | CC `defaultMode` キー将来変更リスク（v2.1.142+ self-grant 防止挙動の永続性） | 現時点では永続前提だが将来覆る可能性あり / 互換性表で追跡 |
| **edit-on-approve** | CC ネイティブ PreToolUse hook 返答仕様に修正値返しがあるか | 未確認 / LangGraph 風 4 値の採用可否を別途調査 |
| **2026-06-30 Cherny announcement** | 個別 announcement の存在と内容 | X HTTP 402 で未確認 / B-5 retro 時に再裏取り |

### 関連 TODO

- C6: LAM hook 障害時 fallback プロトコル（PreToolUse hook が exit 1 で落ちた場合の CC 挙動を upstream で確認）
- D3 適用: サンドボックス化導入時の境界非依存原則の具体化（将来要件）

### 関連 ADR・仕様

- 本 ADR が Accepted になった場合、`docs/specs/approval-gate-v2/` ディレクトリを新設し `compatibility-matrix.md` + Phase B 用 spec を配置
- 重ね掛け撤去判断（Phase C 末）は **新規 ADR-XXXX として再起票**（C4 撤去は不可逆な設計変更のため）

---

## 改訂履歴

| 版 | 日付 | 内容 |
|----|------|------|
| v0.1 (Proposed) | 2026-06-30 | 初版起草（MAGI 合議 AoT B1-B6 + Reflection R1-R4 + Synthesis 反映） |
| v0.2 (Accepted) | 2026-06-30 | PM 一括承認（sougetuOte / 6 軸 + Phase A/B/C + 反面教師制約 D1-D4 + 重ね掛け撤去 3 条件 + 未確認事項 R3/R4 を含む全体）→ Phase A 即時着手可 |
| v0.3 (Accepted・部分撤回) | 2026-06-30 | Phase A 軸 2 自動実行部分（`/quick-load` 1 行サマリ自動表示 + `init-harness` 初回比較表自動表示）を承認 prompt ノイズ過大（`detect-permission-mode.py` 実行毎に Bash 承認発生 → UX 悪化）により **同日内に撤回**。`.claude/scripts/detect-permission-mode.py` 本体は debug / ユーザー手動実行用として温存。Advisory 認知は軸 3 文書（CLAUDE.md + 07_SECURITY_AND_AUTOMATION.md + security-commands.md）で代替。他軸（軸 1 ヘルパー本体 / 軸 3 文書 / 軸 4 LAM 規律核 / 軸 5 反面教師制約 / 軸 6 自己責任モデル境界）は維持。Phase B / Phase C 末計画にも影響なし。 |
