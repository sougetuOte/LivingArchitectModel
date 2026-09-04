## Stage 5: 検証 + Green State 判定 + 完了

**実行条件**: 常に実行
**入力**: テスト結果, lint 結果, `lam-loop-state.json`
**出力**: Green State 判定, ループログ（`logs/`）

### Step 1: G1〜G5 チェック

全修正完了後、Green State 5条件を検証:

1. **G1**: テスト全パス（pytest / npm test 等）
2. **G2**: lint エラーゼロ（設定がある場合）
3. **G3**: 対応可能 Issue ゼロ（PG/SE級は修正済み、PM級は理由付き保留済み）※完全実装
4. **G4**: 仕様差分ゼロ（docs/specs/ と実装の整合性確認）※完全実装
5. **G5**: セキュリティチェック通過（依存脆弱性 + シークレットスキャン）

> **注記**: 回帰テストをサブエージェントに委譲する場合は、フル回帰コマンドと実行件数の期待下限を必ずプロンプトに明示すること（実行範囲漏れの完了報告を防止）。（B-2 retro 反映）

#### 真の Green State の定義

**Green State とは「スキャンして Issue がゼロ」の状態である。「修正後にゼロ」ではない。**

つまり、あるイテレーションで Issue を全件修正しても、それは Green State ではない。
次のイテレーションで再スキャンし、**Stage 2 の監査で新規 Issue が 0件** であって初めて Green State となる。

```
iter 1: 発見 37件 → 修正 37件 → ❌ まだ Green State ではない
iter 2: 発見 19件 → 修正 19件 → ❌ まだ Green State ではない
iter 3: 発見  0件 →             → ✅ Green State 達成
```

この原則により、修正の副作用で生まれた新たな問題が見逃されることを防ぐ。

#### G5 セキュリティチェックの詳細

| チェック項目 | ツール | 判定基準 |
|:---|:---|:---|
| 依存脆弱性 | `npm audit` / `pip audit` / `safety check` | Critical/High 脆弱性ゼロ |
| シークレット漏洩 | **gitleaks**（Stage 1 Step 1.5 で実行済み） | gitleaks Issue ゼロ（`gitleaks:not-installed` 含む） |
| 危険パターン | OWASP Top 10 チェック | eval/exec、SQL文字列結合、pickle.load 等なし |

**gitleaks 未インストール時の G5 判定**: `gitleaks:not-installed` Issue は Critical として扱われるため、**G5 は FAIL** となる。gitleaks をインストールして再実行すれば解消される。インストールガイドは Stage 1 Step 1.5 のログに表示される。

依存脆弱性・危険パターンのツールが未インストールの場合は PASS（スキップ）扱いとし、ログに記録する。
プロジェクトに Anthropic 公式 `security-guidance` plugin がインストールされている場合は、そちらの検出結果も考慮する。

### Step 2: 影響範囲分析（FR-7d）

再レビュー時に `analyze_impact()` で影響範囲を計算し、`classify_impact_for_cards()` で概要カードの再利用判定を行う。
影響範囲外のファイルの概要カード機械的フィールドはハッシュ未変更なら再利用可能。

#### 再レビューループでの Stage 3 再実行（C-3b）

修正後の再スキャン時、Stage 3 も含めて全 Layer をゼロベースで再実行する:

- **概要カード・要約カードも再生成する**（キャッシュしない）
- Layer 2 の境界チェック、Layer 3 の循環依存・命名・仕様ドリフトも毎回再実行
- 静的解析（Stage 1）は変更ファイルのみ再実行（キャッシュ利用）

```
再スキャンフロー:
Stage 1（静的解析: 変更ファイルのみ）
  → Stage 2（チャンク分割: 再実行）
  → Stage 2（並列監査: ゼロベース全体）
  → Stage 3（階層的レビュー: Layer 2→3 全再実行）
  → Stage 4〜5（統合・修正・検証）
```

#### 監査範囲と検証範囲

| ステージ | 範囲 | 目的 |
|---------|------|------|
| Stage 2（監査） | **毎回、対象全体をゼロベース** | 修正の副作用、他エラーに隠れていた問題を発見 |
| Stage 3（階層的レビュー） | **毎回、全 Layer をゼロベース** | カード再生成、構造問題の再検出 |
| Stage 5（テスト・lint） | 変更ファイル中心（最終サイクルで全体） | テスト実行コストの最適化 |

### Step 3: ループ継続/停止判定

**フルスキャンの発動手順**: 差分チェックで Green State を達成したら、Claude が状態ファイルに `fullscan_pending: true` をセットし、自分で Stage 2 に戻る:

```bash
# 差分チェック Green State 達成時に実行
bash .claude/scripts/py_invoke.sh -c "import json,pathlib;p=pathlib.Path('.claude/lam-loop-state.json');d=json.loads(p.read_text());d['fullscan_pending']=True;p.write_text(json.dumps(d,indent=2,ensure_ascii=False))"
```

Claude が `fullscan_pending=true` を確認し、もう1サイクル（フルスキャン）を Stage 2 から実行する。フルスキャンでも Green State なら Step 4（完了報告）に進む。

#### 状態ファイル更新

Stage 4 完了時に `.claude/lam-loop-state.json` を更新する:
- `iteration` をインクリメント
- `log[]` に当該イテレーションの結果（issues_found, issues_fixed, pg/se/pm 件数）を追記

#### ループ継続/停止の判定（Claude 側で制御）

**重要**: ループは Claude が自分で制御する。応答を終了せずに Stage 2 に戻ること。

**絶対ルール: Before=0 を確認するまで終了してはならない。**
修正後に Issue 0件になっても、それは Green State ではない。
次のイテレーションで再スキャン（Stage 2）し、**スキャン結果が 0件** であって初めて Green State となる。

```
Stage 2 + 3（再スキャン: 全 Layer）
  ├── Issue 0件（Before=0、全 Layer 含む）→ ✅ Green State 達成 → Stage 5（完了報告）へ
  └── Issue 1件以上 → Stage 4〜5（修正）→ Stage 2 に戻る（応答を継続）

例外（応答を終了してよいケース）:
  ├── max_iterations 到達 → Stage 5（完了報告）へ
  └── PM級 Issue あり → PG/SE 修正後、PM級を提示して応答を終了（ユーザー判断待ち）
```

**禁止**: 修正完了をもって Green State と見なすこと。必ず再スキャンで Before=0 を確認すること。

**max_iterations 到達時の運用**: Before=0 が未確認のまま max_iterations に到達した場合、上限延長を即承認するのをデフォルト運用とする（Before=0 確認までループを継続。中止する場合のみ明示判断を仰ぐ）。（B-2 retro 反映）

### Step 4: 完了報告 + ループログ出力

```
=== Full Review 完了 ===

イテレーション数: N（最終イテレーションの Before=0 で Green State 確定）
最終イテレーション: Before 0件（スキャンで Issue ゼロ = 真の Green State）
累計修正: Critical X / Warning X / Info X

修正ファイル: X件
テスト: PASSED (X tests)
lint: PASSED
Green State: 達成（Before=0 確認済み）

対応不可 Issue:
- [I-3] <理由> → 追跡先: docs/tasks/xxx.md
```

Green State 確定後（Claude が実行）:
1. `.claude/lam-loop-state.json` を削除（ループ終了）
2. ループログを `.claude/logs/` に保存

---

