# 裏取り結果: `/goal` 機構（T0-1 着手ゲート）

調査日: 2026-05-30 / 担当: Living Architect(Opus) / フェーズ: BUILDING（Wave 0 / T0-1）
対象タスク: [tasks.md](../../../specs/autonomous-mode/tasks.md) T0-1（`/goal` 機構の二段裏取り）
手段: context7（`/websites/code_claude` = code.claude.com/docs）優先 + WebFetch（公式ページ全文）+ `claude --version`

> upstream-first 二段構え（planning-quality-guideline §7）に従い、段階1（実在性）と段階2（LAM 適合性）を分けて評価する。

---

## 段階1: 実在性

| # | 確認項目 | 結果 | ラベル | 出典 |
|---|---------|------|--------|------|
| 1 | `/goal` の実在 | 実在。`/goal <自然言語条件>`。条件は最大4,000字。設定で即ターン開始 | **確認済み** | code.claude.com/docs/en/goal |
| 2 | completion 宣言方法 | 自然言語条件。`or stop after 20 turns` 等で turn/time 上限を条件文に含める | **確認済み** | 同上（Write an effective condition）|
| 3 | evaluator 機構 | **session-scoped prompt-based Stop hook のラッパー**。各ターン後、条件＋会話を小型高速モデル（既定 Haiku）に送り yes/no。no→継続、yes→クリア＋達成記録 | **確認済み** | 同上（How evaluation works）|
| 4 | **evaluator の判定源** | 🔴 *"It doesn't run commands or read files independently"* — **会話の文面しか見ない**（Claude が transcript に出した内容を読むのみ）| **確認済み** | 同上（Write an effective condition）|
| 5 | resumable | ✅ アクティブな goal はセッション終了後 `--resume`/`--continue` で**復元**。条件は引き継ぐが turn数/タイマー/トークンbaseline はリセット。達成済み・クリア済みは復元しない | **確認済み** | 同上（Resume with an active goal）|
| 6 | stuck/thrash 対処 | `/goal` 自体に自動 stuck 検知なし。**条件文に turn/time clause** を書いて bound | **確認済み** | 同上 |
| 7 | モード対応 | interactive / `-p`（headless 完走・Ctrl+C 中断）/ desktop / Remote Control | **確認済み** | 同上（Run non-interactively）|
| 8 | evaluator モデル設定 | 設定可能（small fast model / 既定 Haiku）。session の provider 依存 | **確認済み** | 同上 + /en/model-config |
| 9 | 前提条件 | trust dialog 承認済ワークスペースのみ。`disableAllHooks` / `allowManagedHooksOnly` 時は使用不可 | **確認済み** | 同上（Requirements）|
| 10 | **バージョン要件** | 🔴 **`/goal` は v2.1.139 以降が必須** | **確認済み** | 同上（Note）|
| 11 | **現環境バージョン** | 🔴 **`2.1.126`**（v2.1.139 未満 → 現状 `/goal` 使用不可）| **確認済み** | `claude --version` |
| 12 | script-based Stop hook で決定的チェック | ✅ 任意のコマンド（test/lint 等）を実行し exit 2 または `{"decision":"block"}` で停止阻止＝継続。Stop hook 単体で「ターンまたぎ自律」が成立 | **確認済み** | code.claude.com/docs/en/hooks |
| 13 | `/goal` と settings の Stop hook の共存 | ✅ 両方ターン後に発火。異なるタイプ（prompt vs command）は両方実行 | **確認済み** | docs/en/goal（Compare）+ docs/en/hooks |
| 14 | 複数 Stop hook の block 合成規則 | ⚠️ **公式未文書化**。一般パターンから「いずれか1つでも block → 継続」が保守的安全側として推奨。要経験的検証 | **未確認（要経験的検証）** | docs/en/hooks（明示なし）|

---

## 段階2: LAM 適合性

### 論点A: evaluator の非決定性 vs FR-4.1b

`/goal` の Haiku evaluator は**コマンドを実行せず会話の文面で判定**する（項目4）。これは FR-4.1b「モデルが達成と宣言したことを完了の唯一根拠にしてはならない」と**真っ向から緊張**する。

→ **解決可能**: design D3 が既に「script-based Stop hook が G1/G2/G5 を厳密実行し block」を設計済み（項目12）。決定的判定を LAM の `lam-stop-hook.py` が担えば、`/goal` の Haiku は補助シグナル（FR-4.2 の非決定的観点側）に格下げでき、FR-4.1b を充足する。**ただし design D1 の「/goal の validator が毎ステップ Green State 達成かを問う」という記述は誤解を招くため精緻化が必要**（決定的判定は validator ではなく D3 の script hook が担う）。

### 論点B: v2.1.139+ 必須・現環境 2.1.126 で使用不可

`/goal` は現環境（2.1.126）で**動かない**（項目10/11）。requirements FR-6.2「core の実行手段は /goal ベース」が現状成立しない。

→ **再評価**: 裏取りで「Stop hook 単体でターンまたぎ自律が成立する」「`/goal` は prompt-based Stop hook のショートカットに過ぎない」と判明（項目3/12）。LAM の自律エンジンは **`/goal` に依存せず、script-based Stop hook（決定的 checker + block）だけで実装できる**。これは:
- FR-4.1b を最も純粋に満たす（決定的 checker が直接 gate ＆ ターンまたぎエンジン）
- **バージョン非依存**（v2.1.126 で動く / Stop hook は枯れた機能）
- 論点A（Haiku 非決定性）を回避

### FR-6.2 の真意の再解釈

FR-6.2 の MUST は「dynamic workflows を**必須依存にするな**（$100 Max で完結せよ）」。`/goal` を**必ず使え**という意味ではない。script-based Stop hook は最軽量で $100 Max に収まる。→ FR-6.2 は「軽量な Stop hook ベース（`/goal` もその一形態）」と精緻化すれば真意は保たれる。

---

## 結論と代替設計案（PM級・design/requirements 差し戻しを要する）

| 項目 | 確定状況 |
|------|---------|
| `/goal` 実在性 | ✅ 確定（全仕様判明）|
| resumable（FR-7.1）| ✅ 確定（`--resume`/`--continue`、または autonomous-state.json + quick-save/load）|
| completion 接続（決定的接地）| ✅ 確定（**script-based Stop hook が担う**。`/goal` の Haiku では FR-4.1b 不充足）|
| `/goal` を core にできるか | 🔴 **現環境では不可**（v2.1.139+ 必須・現 2.1.126）|

### 代替案

- **案1（アップグレード）**: Claude Code を v2.1.139+ に上げ、design 維持で `/goal` を core に使う。環境変更（PM）。論点A（Haiku 非決定性）は D3 の script hook で吸収。
- **案2（`/goal` 非依存）**: 自律エンジンを LAM 自前の script-based Stop hook（決定的 checker + block）にする。`/goal` は future-candidates へ。design D1 / FR-6.2 を差し戻し精緻化。
- **案3（ハイブリッド・推奨）**: MVP は案2（script Stop hook エンジン・バージョン非依存・FR-4.1b 純粋）。`/goal` は「v2.1.139+ アップグレード後に**ユーザー完了条件宣言の UX レイヤー**として重ねる」候補を future-candidates に採用再評価条件付きで記録。FR-6.2 は「軽量 Stop hook ベース」と精緻化。

> tasks T0-1 完了条件「段階2 で不整合が判明した場合は理由を future-candidates に記録し、代替手段を design 差し戻しで再検討」に該当。**Wave 1 着手前にユーザー判断（PM）を要する。**

---

## ユーザー決定（2026-05-30）: 案1（アップグレード優先）

- Claude Code を **v2.1.139+ にアップグレード**し、`/goal` を core にする現 design を**維持**する。
- 論点A（Haiku 非決定性 vs FR-4.1b）は design **D3 の script-based Stop hook（決定的 checker + block）が gate** することで吸収する。design D1 の「validator が Green State を問う」記述は精緻化する（決定的判定は validator ではなく script hook が担う）。

### Wave 1 着手の前提条件（本決定により発生）

- **P-1**: Claude Code を v2.1.139+ にアップグレード（現 2.1.126 では `/goal` 使用不可）。環境変更（PM・ユーザー操作）。**アップグレードは Claude Code 再起動＝新セッションで反映**される。
- **P-2**: アップグレード後、`/goal` と `lam-stop-hook.py` の共存・**複数 Stop hook の block 合成**（項目14 の未確認）を**実機で1回検証**してから T1 実装に入る。

---

## T0-1 追加裏取り（2026-05-30 / アップグレード後の精緻化検討）

承認済み ①② に織り込むべき技術制約（A/B）と、新たな設計判断材料（C）が判明。

### A. 🔴 Stop hook の block cap = 8（design D1/D3 に必須追加）

- Stop hook が **8回連続 block すると Claude Code が override してターン終了**（出典: docs/en/hooks「Claude Code overrides the hook and ends the turn after 8 consecutive blocks」/ hooks-guide）。
- hook は入力の **`stop_hook_active`** を見て、既に継続中なら早期 exit して停止を許すべき。
- block cap は環境変数 **`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`** で引き上げ可能。
- **含意**: LAM の `max_iterations`（暫定20）は Stop hook の block cap（既定8）に**上書きされる**。8回超で自律ループを回すには cap 引き上げ＋`stop_hook_active` 連動設計が必須。→ design D1/D3 に明記（①に織り込む）。

### B. exit code / JSON output 仕様（T1-2/T1-3 実装仕様・確定）

- script/command hook: `exit 2`＝block（stderr が Claude へのフィードバック）/ `exit 0`＝no decision（通常の許可フロー）/ `exit 1`＝non-blocking。または JSON `{"decision":"block","reason":...}`。
- prompt hook（`/goal` 内部形式）: `{"ok":false,"reason":...}`。
- → checker(T1-2) は exit 2 + stderr、`lam-stop-hook`(T1-3) は `{"decision":"block","reason"}` で継続指示。

### C. 🟢 auto mode（FR-2 / 3.4 / 9 をネイティブ機構で強化できる発見・新設計判断）

- `claude --permission-mode auto`：classifier が各 tool call を分類し、**不可逆・破壊的・環境外指向を block**（出典: docs/en/auto-mode-config, permission-modes, best-practices）。
- 4層 precedence: `hard_deny`（無条件・user intent も効かない）> `soft_deny`（intent/allow で上書き可）> `allow` > explicit user intent。
- 🔑 **`permissions.deny`（managed settings）は classifier の前に走り、上書き不可**（"blocks the action before the classifier is consulted and cannot be overridden"）。
- **LAM 適合性（段階2）**: auto mode は LAM の権限思想と高度に整合する。
  - auto mode classifier ＝ FR-2.1 PG 無断実行 ＋ 不可逆 block の自動化
  - auto mode `hard_deny` / `permissions.deny` ＝ FR-3.4 C層・即時ハードストップ
  - **`permissions.deny`（上書き不可）＝ FR-9.1 MUST NOT の決定的強制点**（現 design D5 の PreToolUse hook より堅牢。classifier より前段）
  - `/goal`（per-turn）＋ auto mode（per-tool）＋ script Stop hook（決定的 checker）＝ 三位一体
  - ⚠️ 制約: auto mode は **Anthropic API のみ**（Bedrock/Vertex/Foundry 不可）。ユーザー環境（Max 5x）の可用性を要確認。classifier 自体は非決定的なので、決定的強制は `permissions.deny` 側に置く。

### D. 複数 Stop hook の block 合成（→ P-2 実機検証で確定: OR / most-restrictive）

- T0-1 時点では公式未明示。**P-2 実機検証（2026-05-30）で「いずれか1つでも block→継続」（OR）を確定**。詳細は下記「P-2 実機検証結果」。

### E. ✅ auto mode 可用性確認（`claude auto-mode config`）+ デフォルトルールの LAM 整合

- **本環境で auto mode 利用可能**（effective config を取得。Max 5x = Anthropic API 経由）。
- 🔑 **auto mode デフォルト `soft_deny` が LAM の権限思想とほぼ一致**:
  - **"Self-Modification"**: `.claude/settings*.json` / `CLAUDE.md` / `.claude/rules/` / `.claude/hooks/` / `.claude/skills/` / `.claude/agents/` / `.claude/commands/` 等への自己改変、permission allow ルールの拡張をブロック → **FR-9.1 とほぼ同一**
  - **"Irreversible Local Destruction"**: `rm -rf` / `git clean -fdx` / `git reset --hard` 等（specific target 指定なし）→ FR-3.4
  - **"Create Unsafe Agents"**: `--dangerously-skip-permissions` / 承認ゲート無効化での自律ループ生成をブロック → **LAM autonomous は「established safety framework」（1回承認＋決定的checker＋permissions.deny＋PMキュー）として正当化が必要**。ADR-0005「autonomy with a constitution」と一致
  - **"Git Destructive" / "Git Push to Default Branch"** → FR-3.2 / 3.4
  - **"Credential Leakage / Exploration"** → G5
  - allow 側: "Local Operations"（project scope 内）/ "Git Push to Working Branch"（session 作成ブランチ）/ "Memory Directory"（agent-memory 書込）/ "Read-Only Operations" → FR-2.1 PG無断・B層と整合
- ⚠️ **重要な区別**: auto mode の Self-Modification は **soft_deny（user intent / allow で上書き可）**。FR-9.1 の MUST NOT を保証するには **`permissions.deny`（上書き不可・classifier 前段・"cannot be overridden"）に明示配置**する（ユーザー決定「段階的統合」と一致）。
- **段階2 結論**: auto mode は LAM 思想と高度に整合。MVP は **permissions.deny に FR-9/C層を固定**（決定的・上書き不可）、auto mode classifier は FR-2 の利便レイヤーとして重ねる。LAM autonomous は承認ゲート＋決定的 checker＋permissions.deny を備えることで "Create Unsafe Agents" の例外（安全枠組み）として成立する。

---

## 裏取り総括（T0-1 完了判定）

| 項目 | 状況 |
|------|------|
| 段階1 実在性 | ✅ 完了（`/goal` v2.1.139+・evaluator 非決定的・resumable・block cap=8・exit code 仕様・auto mode 可用）|
| 段階2 LAM 適合性 | ✅ 完了（決定的接地は script hook、FR-9 は permissions.deny、auto mode は段階的統合）|
| 未確認の残 | 項目14（複数 hook の block 合成）→ **P-2 実機検証**に限定。他は確定 |
| 反映先 | design: D1 精緻化 + block cap(A) + exit code(B) + 新節 auto mode(C)。tasks: 前提条件 P-1/P-2 + T1-2/3/4 仕様強化 |

---

## P-2 実機検証結果（2026-05-30 / Wave 1 着手ゲート）

再起動後（**2.1.158**）に T0-1 で残した3点を確定。手段: context7 再取得 + `claude auto-mode config` + 隔離 headless 実機検証（`claude -p`）。

### P-2a: block cap（確定）

- `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`（既定 **8** / **`0` で無効化**＝新情報）・「8 consecutive blocks で override」・`stop_hook_active` 早期 exit を公式再確認（`/en/hooks`・`/en/env-vars`・`/en/hooks-guide`）。本環境の同変数は **unset**（＝既定 8）。

### P-2b: auto mode（確定）

- `claude auto-mode config` が effective config を JSON 出力（**2.1.158 動作確認**）。
- 🔑 **`permissions.deny` は classifier 前段・override 不可**を公式明記で確認（`/en/auto-mode-config`: *"blocks the action before the classifier is consulted and cannot be overridden"*）→ **D7 層1（FR-9.1 決定的強制点）の裏取り完了**。
- デフォルト `soft_deny` に **Self-Modification**（`.claude/{settings*.json,rules,hooks,skills,commands,agents,workflows,routines}`・`.mcp.json` 等）/ **Create Unsafe Agents**（*established safety frameworks* 例外を明記）/ **Irreversible Local Destruction** を確認。soft_deny は user intent/allow で**上書き可** → FR-9.1 MUST NOT 保証には層1 `permissions.deny` 固定が必須（§E を公式が補強）。

### P-2c: 複数 Stop hook の block 合成（実機確定）🔑

- **方法**: プロジェクト外の使い捨て `stophook-probe` に **2つの別エントリ** script Stop hook（`hook_block`=`decision:block` / `hook_stop`=`exit 0`）を共存させ、`claude -p "...done"` を headless 実行。`hook_block` は `stop_hook_active=true` で早期 exit（暴走防止）。
- **結果**（`probe.log` 4行 / `num_turns:2` / `stop_reason:end_turn` / `permission_denials:[]`）:
  - ターン1: `hook_block`(block) と `hook_stop`(stop) が**両方発火**（`stop_hook_active=False`）→ **ターン継続**。
  - ターン2: 両 hook に `stop_hook_active=True` → `hook_block` 早期 exit → **停止**。
- **確定**: 複数 Stop hook の合成は **「いずれか1つでも block→継続」（OR / most-restrictive）**。項目14 の保守的安全側仮説が実機で成立。
- **設計含意**: LAM の決定的 `lam-stop-hook`(block) は `/goal` evaluator(stop) と共存しても **block が勝つ**＝決定的 checker が完了 gate を維持（FR-4.1b 充足）。**D1/D3 の前提が成立**。
- **限定と推論**: 検証は script×script。prompt×script は型非依存の decision マージ（公式は hook type 別の合成規則を記述せず）から同じ OR と推論。`/goal` 実起動での確認は Wave 1 の T1-3 実装時に実地でも可能。

### Wave 1 着手判断

- P-2 の核心懸念（evaluator 誤判定で決定的 gate が破られる）は **否定＝安全側**。Wave 1 着手の技術的前提は全て充足。
- 残作業（PM）: design D1/D3・tasks P-2 の「実機検証する」記述を「実機確定（OR）」へ更新。
