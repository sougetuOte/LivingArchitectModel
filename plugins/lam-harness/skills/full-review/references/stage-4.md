## Stage 4: トポロジカル順修正

**実行条件**: 常に実行
**トポロジカル順修正**: `scale-detection.json` の `active_plans` に `"D"` が含まれ、かつ `dependency-graph.json` が存在する場合はトポロジカル順で修正。それ以外は重要度順で修正。
**入力**: 統合レポート, `dependency-graph.json`（任意）
**出力**: 修正済みコード

承認後、権限等級に応じて修正:

- **PG級**: 自動修正（承認不要）— フォーマット、typo、lint 修正等
- **SE級**: 修正 + ログ記録 — テスト追加、内部リファクタリング等
- **PM級**: **ループ一時停止 + ユーザー判断待ち** — 仕様変更、アーキテクチャ変更等

### Step 0: 帰責ヒント付き Issue のガード（FR-4）

修正開始前に、帰責ヒント付き Issue を以下のルールで振り分ける:

- `suspected_responsible` が `spec_ambiguity` → **自動修正しない**。PM級としてユーザーに提示
- `suspected_responsible` が `upstream` または `downstream` → 帰責ヒントを添えてユーザーに修正方針の確認を求める。ただし `.claude/rules/permission-levels.md` の PG 級に該当する修正（フォーマット、typo、lint 違反等）は帰責ヒントに関わらず自動修正可
- `suspected_responsible` が `unknown` または帰責ヒントなし → 従来通りの重要度ベース修正

帰責判断の詳細フローチャートは `.claude/rules/code-quality-guideline.md` の「モジュール間帰責判断」セクションを参照。

### Step 1: PG/SE 級修正（トポロジカル順）

依存グラフが存在する場合（`dependency-graph.json`）、修正順序をトポロジカル順にする:
- `order_files_by_topo(file_paths, topo_order, node_to_file)` で修正対象ファイルをソート
- 上流モジュールから修正し、下流への波及を最小化する
- 依存グラフがない場合は従来通り Issue 重要度順で修正

### Step 2: PM 級処理フロー

PM級の Issue が存在する場合、**`auto_approve` 状態により挙動が分岐する**:

#### auto_approve=false（通常モード）

PG/SE級を先に修正した後、以下の手順でユーザーの判断を仰ぐ:

1. PG/SE級を通常通り修正
2. PM級の Issue 一覧と修正案をユーザーに提示
3. `pm_pending: true` を状態ファイルにセット
4. 応答を終了（Stop hook は `pm_pending=true` を検出し、block せずに停止を許可）
5. ユーザーが条件付き承認・修正指示・却下などを返答
6. 指示に従い PM級を修正
7. `pm_pending: false` を状態ファイルにセット + 応答終了
8. Claude が応答を再開し、Stage 2 に戻って再監査

```bash
# PM級 Issue 発見時に実行（通常モード）
bash .claude/scripts/py_invoke.sh -c "import json,pathlib;p=pathlib.Path('.claude/lam-loop-state.json');d=json.loads(p.read_text());d['pm_pending']=True;p.write_text(json.dumps(d,indent=2,ensure_ascii=False))"
```

```bash
# PM級修正完了後に実行（通常モード）
bash .claude/scripts/py_invoke.sh -c "import json,pathlib;p=pathlib.Path('.claude/lam-loop-state.json');d=json.loads(p.read_text());d['pm_pending']=False;p.write_text(json.dumps(d,indent=2,ensure_ascii=False))"
```

#### auto_approve=true（サブエージェントモード）

PM級 Issue がある場合、**pm_pending をセットせず**、構造化 JSON を stdout に出力してスキルを終了する:

```bash
# auto_approve=true 時: PM級 Issue 一覧を JSON stdout に出力して終了
# pm_pending は true にしない（Stop hook 経由ループバック禁止）
# [PM_ISSUES_JSON] は PM級 Issue を JSON 配列にシリアライズした文字列で置換すること
bash .claude/scripts/py_invoke.sh -c "
import json, sys
pm_issues = [PM_ISSUES_JSON]
result = {
  'pm_issues': pm_issues,
  'status': 'pm_pending',
  'invocation_id': None
}
print(json.dumps(result, ensure_ascii=False, indent=2))
sys.exit(0)
"
```

出力スキーマ例:
```json
{
  "pm_issues": [
    {"id": "C-1", "severity": "Critical", "level": "PM", "file": "src/foo.py", "line": 42, "message": "..."}
  ],
  "status": "pm_pending",
  "invocation_id": null
}
```

呼び出し元（上位エージェント等）はこの JSON を解析し、PM級 Issue をユーザーに提示してから修正方針を決定する。

共通ポリシー:
- **A-1**: Critical / Warning に対応する。Info は参考情報であり修正不要（`code-quality-guideline.md` 準拠）。Critical/Warning の defer（先送り）は原則禁止（PM級 Warning のみ理由付き deferred を許可）
- **A-2**: **スコープ外 Issue の扱い** — 以下の条件を**すべて**満たす場合のみ、当該イテレーションでの修正を免除できる:
  1. 依存先が未実装（別 Phase/Wave のスコープ）等、**技術的に着手不可能**であること
  2. 「コンテキスト不足」「工数が多い」「面倒」は理由にならない。コンテキスト逼迫時は `/quick-save` でセッション分割せよ
  3. スタブや暫定対策で塞げる場合はその場で実施すること
  4. 免除する場合は **理由 + 対象 Wave/Phase + 追跡 Issue（`docs/tasks/` に起票）** を明記
  5. 免除 Issue は完了報告に件数・一覧を含めること（黙って消えることを許さない）
- **A-3**: 仕様ズレが発見された場合は `docs/specs/` も同時修正
- **A-4**: 修正は1件ずつ、テストが壊れないことを確認しながら進める
- **A-5**: 対称性（防御・ログ・エラー処理の非対称）を修正した場合は、同型の非対称が他ファイル・他関数に残っていないか grep で横展開確認を行う（B-2 retro 反映）

---

