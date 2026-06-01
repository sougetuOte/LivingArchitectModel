---
name: autonomous
description: "AUTONOMOUSフェーズを開始 - 対象 spec を Green State(G1) まで自律実装（MVP/Wave 1）"
version: 1.0.0
disable-model-invocation: true
---

# AUTONOMOUSフェーズ開始（MVP / Wave 1）

あなたは今から **[AUTONOMOUS]** モードに入ります。
対象 spec を入力に取り、人間の逐次承認なしに build → 決定的 checker(G1) → 完了までを
ターンをまたいで自律的に進めます（ADR-0005「autonomy with a constitution」）。

> **このモードは「承認された安全枠組み」内でのみ成立する**（FR-9 / D7）:
> 起動時の 1 回承認 + 決定的 checker による完了 gate + `permissions.deny`（統治ファイル
> 上書き不可）+ PM 境界。これらを欠いた無断の自律ループ起動は禁止（"Create Unsafe Agents"）。

## 起動引数

```
/autonomous <spec_target>
```

- `<spec_target>`: 対象 spec のパス（例: `docs/specs/<feature>/requirements.md`）。

## 前提条件（起動前に確認）

1. **`/goal` 利用可**: Claude Code v2.1.139+（現環境 2.1.158 で確認済）。trust dialog 承認済み
   ワークスペースであること（`disableAllHooks` / `allowManagedHooksOnly` 時は使用不可）。
2. **層1 deny の起動注入（FR-9.1 決定的層・T1-4 層1）**: autonomous セッションは
   **`claude --permission-mode auto --settings .claude/settings.autonomous.json`** で起動する。
   これにより統治ファイル（`FR9_PATTERNS`）への書込が `permissions.deny`（CLI scope・
   deny-first・override 不可）で決定的に block される。共有 `.claude/settings.json` には
   置かない（自己ロック回避）。**起動・再開（`--resume`/`--continue`）とも常にこのフラグを付ける**
   （付けないと層1 が無効化。FR-7.1）。
3. **block cap 引き上げ**: Stop hook は 8 回連続 block でターン終了する（既定 cap=8）。
   `max_iterations`（既定 20）を活かすため、起動前に環境変数
   **`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`** を `max_iterations` 以上、または **`0`（無効化）**
   に設定する（これは起動時の環境設定でありユーザー操作）。
4. **人間監視下での実証**: MVP は権限エンベロープ（FR-2）・PM キュー（FR-3）・last-line
   自己起動（FR-5.6）が**未実装**。人間が監視しながら実施すること（tasks.md Wave 1 注意）。

## 実行ステップ

### 1. 起動引数の検証 + 層1 自己点検（fail-safe）
- `<spec_target>` が指定され、ファイルが実在することを確認する。不在なら起動を中止し、対象 spec のパスを尋ねる。
- **層1 deny の有効性を自己点検する**: `.claude/settings.autonomous.json` が存在し、`--settings` で
  注入されているか確認する（例: `claude auto-mode config` の effective config に統治ファイルの deny が
  含まれるか）。`--settings` 付け忘れ等で層1 が無効なら **警告して中止**する（層2=phase 条件 deny は
  残るが、決定的層を欠いたまま自律ループに入らない）。

### 2. 完了条件の提示（MVP = G1）
- MVP の完了条件は **G1（テスト全 PASS）** のみ。決定的 checker
  [`check_g1_test.py`](../../hooks/checkers/check_g1_test.py) が exit 0 を返すことが完了の唯一の決定的根拠。
- G2(lint) / G5(security) / G3(Issue) / G4(仕様差分) は MVP スコープ外（後続 Wave）。
- 完了条件・`max_iterations`・block cap 設定状況をユーザーに明示する。

### 3. 承認ゲート（1 回承認・FR-1.2）
- 以下を提示し、ユーザーの**明示的な承認**（「承認」入力）を得る。承認まで自律ループに入らない。
  - 対象 spec
  - 完了条件（G1: テスト全 PASS）
  - `max_iterations`（既定 20）/ `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` の設定状況
  - 起動する `/goal` 条件文（下記）

### 4. セットアップ（承認後）
> この順序を守る。状態を AUTONOMOUS に切り替えると FR-9 deny が有効化されるため、
> 統治ファイルに触れる準備は不要（MVP のループは触れない）。

1. **`autonomous-state.json` を生成**（schema の SSOT は
   [`autonomous_state.py`](../../hooks/autonomous_state.py) `build_initial_state`。直書きで drift させない）:
   ```bash
   python -c "import sys; sys.path.insert(0, '.claude/hooks'); import json, autonomous_state as a; from pathlib import Path; s = a.build_initial_state('<spec_target>'); Path('.claude/autonomous-state.json').write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding='utf-8')"
   ```
   生成後 `active=true` / `phase="building"` / `spec_target` 一致を確認する。
2. **`.claude/current-phase.md` を `AUTONOMOUS` に更新**（`**AUTONOMOUS**` 行。値の登録は T1-6）。

### 5. ループ engagement（`/goal` ベース・FR-6.2）
- ユーザーに次の `/goal` 起動を案内する（ターンまたぎ自律エンジン兼・完了条件宣言の UX）:
  ```
  /goal "<spec_target> の Green State 条件 G1（lam-stop-hook の G1 test checker が exit 0）を達成する。or stop after 20 turns"
  ```
- `/goal` の evaluator（既定 Haiku）は**会話の文面のみで非決定的に判定する**。これを完了の
  唯一根拠にしない（FR-4.1b）。**決定的な完了 gate は script Stop hook
  [`lam-stop-hook.py`](../../hooks/lam-stop-hook.py) の G1 checker 厳密実行が担う**。
  複数 Stop hook の block 合成は OR（いずれか block→継続）で確定済（findings P-2c）であり、
  決定的 hook が `/goal` evaluator に優先する。
- `or stop after N turns`（N=`max_iterations`）で stuck を bound する（`/goal` 自体に stuck 検知なし）。

### 6. 駆動（build サブルーチン → checker → 反復）
- 既存 **building スキルは変更せず**、その作法（TDD: Red→Green→Refactor / 仕様同期）を
  **内側で駆動**する（ADR-0005 CASPAR 方針5・in-place 独立）。
- build 区切り／completion を主張して停止しようとすると Stop hook が発火し、
  `lam-stop-hook` が G1 checker をサブプロセス厳密実行して実 exit code を
  `checker_results.g1_exit` に記録（モデル改竄不能・D3）:
  - **G1 FAIL（exit≠0）** → `{"decision":"block"}` でループ継続。`iteration` を +1 し
    `phase="building"` に戻し、赤の詳細を手がかりに修正する。
  - **G1 PASS（exit 0）** → `active=false` / `phase="done"` にして completion 許可。
- `iteration >= max_iterations` 到達でも `active=false` 停止（無限ループ防止）。

### 7. 終了（完了報告）
- `lam-stop-hook` が `active=false` にしたら完了。以下を報告する:
  - 達成した完了条件（G1 PASS）/ 総 iteration 数 / `checker_results`
  - `max_iterations` 到達で停止した場合はその旨（未達）
- SE バッチ報告（FR-2.2）・`pm_queue` 一括審議（FR-3）・last-line（FR-5.6）は
  **後続 Wave で追加**（MVP スコープ外）。

## モデル委譲方針（FR-6.1）

- 自律ループ**本体は下位モデル / 低 effort**（例: Sonnet / 低）で回す（$100 Max 制約）。
- **難所のみ Opus / 高 effort に上げる**（G1 が連続 FAIL・想定外エラー・設計分岐等）。
  難所の自己起動（MAGI / full-review）は Wave 4 で実装。MVP は方針の明示に留め、
  難所では人間が監視下でモデルを上げる。

## FR-9 制約（自己統治の不可侵・二重防御）

AUTONOMOUS 下では、自律エンジンが自身の統治を定義するファイル群への**書込が deny**される
（自己破壊的再帰の防止）。これらの変更は常に自律ループの**外側の人間承認ゲート（PM）**を経由する。

- 対象（`FR9_PATTERNS`）: `.claude/rules/**` / `docs/adr/**` / `.claude/settings*.json` /
  `.claude/hooks/**` / `.claude/skills/autonomous/**`（**このスキル自身を含む**）。
- 二重防御: プロンプティング層 = PreToolUse hook（[`pre-tool-use.py`](../../hooks/pre-tool-use.py)・
  AUTONOMOUS 限定 deny）/ 決定的層 = `permissions.deny`（[`settings.autonomous.json`](../../settings.autonomous.json) を
  `--settings` 注入・classifier 前段・上書き不可・T1-4 層1）。`Edit`+`Write` 併記で MUST NOT 境界を防御。

## MVP スコープ外（後続 Wave で実装）

| 項目 | FR | Wave |
|------|----|----|
| 権限エンベロープ（PG無断 / SE蓄積 / PM分岐）| FR-2 | Wave 2 |
| checker G2(lint) / G5(security) 拡張 | FR-4 | Wave 2 |
| PM キュー（可逆 PM のバッチ + merge前ゲート）| FR-3 | Wave 3 |
| last-line 自己起動（MAGI / full-review・予算）| FR-5.6 | Wave 4 |
| quick-save 統合（resumable）| FR-7.1 | Wave 5 |

> 不可逆 C（rm / push / 秘密露出 / 統治ファイル書換）の即時ハードストップは
> 既存 deny + FR-9 強制で MVP 時点から成立（FR-3.4）。

## 禁止事項

- 起動承認なしの自律ループ開始（FR-1.2）
- `/goal` evaluator の自己宣言を完了の唯一根拠にすること（FR-4.1b）
- AUTONOMOUS 下での統治ファイル（`FR9_PATTERNS`）の書込（FR-9.1）

## 確認メッセージ（起動承認の提示例）

```
[AUTONOMOUS] モードの起動準備ができました。

対象 spec : docs/specs/<feature>/requirements.md
完了条件   : G1（テスト全 PASS / lam-stop-hook の G1 checker が exit 0）
上限       : max_iterations=20
層1 deny   : settings.autonomous.json [有効/無効]（無効なら起動中止）
block cap  : CLAUDE_CODE_STOP_HOOK_BLOCK_CAP=[0 または 20以上 / 未設定なら警告]

起動する /goal 条件:
  /goal "<spec_target> の Green State 条件 G1 を達成する。or stop after 20 turns"

注意（MVP / 人間監視下）:
- 権限エンベロープ・PM キュー・last-line 自己起動は未実装
- 決定的完了 gate は lam-stop-hook の G1 checker（モデル改竄不能）

承認する場合は「承認」と入力してください。
```

## 権限等級

- 本スキル（モード定義）の追加・変更: **PM級**（モード追加）。
- 自律ループ内の各操作は権限エンベロープ（Wave 2・FR-2）で PG/SE/PM 判定（既存
  `permission-levels.md` と PreToolUse 分類を再利用）。

## 参照

- 仕様: [requirements.md](../../../docs/specs/autonomous-mode/requirements.md) /
  [design.md](../../../docs/specs/autonomous-mode/design.md)（D1/D3/D5/D7）/
  [tasks.md](../../../docs/specs/autonomous-mode/tasks.md)（T1-5）
- 裏取り: [findings.md](../../../docs/artifacts/research/2026-05-30-goal-survey/findings.md)（`/goal` / block cap / OR 合成）
- Green State: [green-state-definition.md](../../../docs/specs/green-state-definition.md)
- 決定: [ADR-0005](../../../docs/adr/0005-thin-harness-autonomous-governance.md)
