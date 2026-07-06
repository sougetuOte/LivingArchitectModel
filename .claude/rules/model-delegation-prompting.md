# モデル別委譲プロンプト指針 (Sonnet 5 / Haiku 4.5)

**制定日**: 2026-07-07
**対象**: 3.5 層委譲モデル (`CLAUDE.md` §作業体制) の L2 (Sonnet) / L3 (Haiku) 委譲プロンプト全般
**出典**: 公式 "Prompting Claude Sonnet 5" + "What's new in Claude Sonnet 5" (platform.claude.com / 2026-07-07 取得) / community 実運用報告 (HN launch thread / CodeRabbit 実測 / claudefa.st 他 / 2026-06-30〜07-03)。調査記録は本ファイル制定セッション (2026-07-07) の 2 系統並列調査による。

## §1 Sonnet 5 の挙動デルタ (4.x 比 / 委譲影響順)

| # | デルタ | 出典 | 委譲への影響 |
|---|--------|------|------------|
| 1 | **リテラル解釈**: 指示をアイテム間で暗黙一般化しない / 依頼外を推論しない ("does not silently generalize / does not infer requests you didn't make") | 公式 | 適用範囲の明示が必須 (「最初の 1 件だけでなく全て」式) |
| 2 | **effort 遵守が厳格** (low/medium は「言われた分だけ」に絞る) / Sonnet 5 の medium ≈ 4.6 の high 相当 | 公式 | 多段推論・TDD 委譲は high 以上 |
| 3 | **実装詳細の over-delivery** (依頼外 helper・テスト・依存追加 / 「boilerplate だけ書け」無視の報告) | community (2+ 独立源) | 下方向フェンス (do NOT 境界) + 親側 diff 検証 |
| 4 | **否定形制約の drop-through** (「install するな」が無視された報告複数) | community | 重要制約は task prompt 内に再掲 (CLAUDE.md 頼み禁止) + 親検収 |
| 5 | adaptive thinking 既定 ON + 新トークナイザで **同一テキスト ~30% トークン増** | 公式 | 予算・max_tokens 見積の再校正 |
| 6 | **レビュー系で recall 低下**: 「高重要度のみ報告」指示をリテラルに実行し絞り込む (4.6 は低重要度も報告していた) | 公式 + community (CodeRabbit 実測: catch 率 63%→50%) | coverage 目的は loose 指示 (§3) |
| 7 | sampling params (temperature / top_p / top_k) は **400 エラー** | 公式 | 委譲設定・API 呼び出しに含めない |

### リテラル × over-delivery の両立解釈 (本指針の核)

デルタ 1 と 3 は矛盾しない: **指示された作業スコープにはリテラル** (明示されない範囲へ広げない) だが、**スコープ内の実装詳細は過剰化しがち** (余計な helper・テスト・防御コード)。よって委譲プロンプトは:

- **上方向 (適用範囲) は明示的に広げる** — 全称・列挙でスコープを書く
- **下方向 (成果物の種類) は明示的にフェンスする** — 変更可ファイル白リスト + 依頼外成果物の禁止列挙

の両建てで書く。

## §2 Sonnet 5 委譲プロンプト必須 7 項

`hga-summoning.md` §tight brief 5-slot (objective / output format / tool guidance / task boundaries / primary_sources) を基底とし、以下を追加・強化する:

1. **スコープ全称明示**: 広く適用させたい範囲は列挙または全称で明示 (公式例: "Apply this formatting to every section, not just the first one")
2. **下方向フェンス**: 変更してよいファイルの白リスト + 「新規依存追加禁止 / 依頼外 helper 禁止 / 依頼外ファイル作成禁止 / git 操作禁止」を明記
3. **肯定形優先**: 「やること」を肯定形で書く (公式: positive > negative)。ただしデルタ 4 により否定形フェンスも併記し、遵守は親側検収で担保する (二重化)
4. **出力契約**: 返却形式を構造で指定 (JSON / 表 / セクション構成)。「まとめて報告して」は書かない
5. **Direct Executor boilerplate**: `hga-summoning.md` §Sonnet L2 委譲時の追加防御 (A + C) — 継続有効
6. **grounding bolt-on**: 同上 — 継続有効
7. **親側検収の予告**: 「diff は親 (L1) が検証する。変更ファイル一覧と境界からの逸脱を自己申告せよ」を明記 (デルタ 3/4 対策の最終防衛線)

## §3 coverage 型 (敵対レビュー) の唯一例外

デルタ 6 により、Sonnet 5 に監査・レビューを委譲する際に「重要なものだけ報告せよ」と書くと recall が下がる。coverage 目的の敵対レビューでは公式推奨文をそのまま使う:

```
Report every issue you find, including ones you are uncertain about or
consider low-severity. Do not filter for importance or confidence at this
stage - a separate verification step will do that. Your goal here is
coverage: it is better to surface a finding that later gets filtered out
than to silently drop a real bug.
```

これは `hga-summoning.md` §loose brief の唯一例外と同一原則 — 継続有効。逆に **精密実行タスクで loose に書くことは禁止** (デルタ 1 により narrow 解釈で under-deliver する)。

## §4 Haiku 4.5 委譲指針

- 公式ドキュメントに Sonnet 5 型「リテラル解釈」の明記は**ない** (未確認事項) — 保守的に Sonnet 5 と同じ明示スコープ・明示出力契約で扱う
- Claude 4.x 世代共通の「precise instruction following」は適用: 3.x 的な「気を利かせる」挙動は期待せず、必要な挙動は全て明示する
- 適所: 分類 / 事実突合 / 構造化抽出 / rubric 採点 / 「実行 + 結果パース + 構造化報告」の複合作業 (既存運用と整合)
- 出力形式 (JSON / CSV / markdown) は厳密指定。境界も明示 (「与えられたデータのみ分析、外部取得禁止」等)

## §5 既存規律との整合・未確認事項

- **`hga-summoning.md` の「Sonnet 5 は loose brief で under-deliver するため下調べ用途に不適」**: 公式のリテラル特性からの帰結として妥当。community 実測では「実装詳細の over-delivery」が優勢だが、これは§1 の両立解釈の通り矛盾しない。下調べ不適判定は**当面維持** (retrieval 主体タスクは Opus 優位という独立根拠あり) — W-R5 retro で再評価
- **「background meta-response 早期終了」(2026-07-04 Wave C 実測)**: community 裏付けゼロ (2026-07-07 調査時点)。Sonnet 5 モデル特性ではなく CC harness (v2.1.198 background 既定) 起因の可能性が高い。対策 (`disallowedTools: [Agent]` + boilerplate) は原因不問で有効なため**継続**
- **未確認事項** (使用時に要実測): Haiku 4.5 の effort param 可否 / Haiku 4.5 への adaptive thinking 適用有無 / トークナイザ 30% 増のコンテンツ種別ごとの実際値

## 権限等級

本ファイルの変更: **PM級**

## 参照

- `.claude/rules/hga-summoning.md` (§tight brief 5-slot / §Sonnet L2 委譲時の追加防御 / §loose brief の唯一例外)
- `CLAUDE.md` §作業体制 (3.5 層委譲モデル) / §担当層の判断基準
- 公式: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5
- 公式: https://platform.claude.com/docs/en/about-claude/models/whats-new-sonnet-5
- 公式: https://code.claude.com/docs/en/sub-agents
- community: https://www.coderabbit.ai/blog/claude-sonnet-5-review (レビュー recall 実測) / HN launch thread (over-delivery / 制約 drop-through 報告)
