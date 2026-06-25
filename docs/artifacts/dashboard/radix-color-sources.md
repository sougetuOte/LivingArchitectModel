# Radix Colors 出典記録 + 手動スクショ取得手順（W6-B5-T32 / VP-2）

- 作成日: 2026-06-25
- 対応タスク: W6-B5-T32
- ステータス: AI 転記完了 / ユーザー手動スクショ取得待ち

---

## §1 概要: なぜスクショ照合が必要か

tasks.md §7 R-1「Radix Colors 値転記誤り（96 値手動入力）/ 影響度: 中」への対応として、
公式ページのスクリーンショット目視照合が必要。

AI エージェントは GitHub リポジトリの `src/light.ts` / `src/dark.ts` から値を取得した。
これらは npm パッケージ（`@radix-ui/colors`）の生成元ソースだが、`main` ブランチ最新値と
npm 公開バージョンの間に一時的なズレが生じる可能性がある。

公式ドキュメントページ（https://www.radix-ui.com/colors）に表示される値と
目視照合することで、誤転記を検出する（VP-2: AI 主導転記 + 人間スクショ照合の分業体制）。

---

## §2 取得済みソース

### GitHub ソース URL

| テーマ | URL |
|--------|-----|
| ライト | https://github.com/radix-ui/colors/blob/main/src/light.ts |
| ダーク  | https://github.com/radix-ui/colors/blob/main/src/dark.ts |

### 取得日

2026-06-25（LAM L1 エージェントが `urllib` で取得 / `C:\Users\metral\radix-values.json` に保存）

### 転記先ファイル

`.claude/scripts/dashboard/_radix_colors.py`

- `RADIX_LIGHT`: gray/blue/green/amber × 12 step = 48 値
- `RADIX_DARK`: gray/blue/green/amber × 12 step = 48 値
- 合計: 96 値

### コミットハッシュ確認手順

取得時点の `main` ブランチのコミットハッシュを確認するには以下を実行する:

```bash
gh api repos/radix-ui/colors/commits/main --jq .sha
```

実行結果を SESSION_STATE.md の「T32 取得コミットハッシュ」欄に記録しておくと、
将来の値更新時に差分を追跡できる。

---

## §3 ユーザー手動スクショ取得手順

以下の手順で公式ページのスクリーンショットを撮影し、転記値と目視照合する。

1. ブラウザで https://www.radix-ui.com/colors を開く

2. gray / blue / green / amber スケールを順に表示し、step 1〜12 の hex 値を確認する
   （各スケールをクリックすると詳細が展開される場合はクリックして全 step を表示）

3. **ライトモードでスクショ撮影**
   - ファイル名: `docs/artifacts/dashboard/radix-colors-light-2026-06-XX.png`
   - `XX` は撮影日（例: 25）

4. ブラウザ DevTools で `prefers-color-scheme: dark` を emulate する
   - Chrome: DevTools → Rendering タブ → "Emulate CSS media feature prefers-color-scheme" → dark

5. **ダークモードでスクショ撮影**
   - ファイル名: `docs/artifacts/dashboard/radix-colors-dark-2026-06-XX.png`

6. SESSION_STATE.md に以下を記録する:
   ```
   T32 VP-2 スクショ取得: OK
   照合結果: 96 値目視一致（または NG の場合は不一致箇所を列記）
   取得日: 2026-06-XX
   ```

---

## §4 既知ズレ可能性

以下の点に注意して照合を行うこと:

| リスク | 説明 |
|--------|------|
| npm 公開値と GitHub `main` の同期ズレ | npm パッケージ（`@radix-ui/colors`）の最新バージョンが `main` より古い場合、公式ページの表示値と GitHub ソースの値が異なることがある |
| Radix Themes 上位レイヤー命名との混同 | 公式ページには `--gray-app` / `--gray-subtle` 等の意味ベース変数（Radix Themes の上位レイヤー）も表示される。転記対象は `--gray-1`〜`--gray-12` 形式の生スケール変数のみ |
| P3 色域値との混同 | 公式ページには sRGB hex 値と P3 oklch 値の両方が表示されることがある。転記対象は sRGB hex（`#xxxxxx` 形式）のみ |
