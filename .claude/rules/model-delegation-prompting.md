# モデル別委譲プロンプト指針 (Sonnet 5 / Haiku 4.5)

**制定日**: 2026-07-07
**対象**: 3.5 層委譲モデル (`CLAUDE.md` §作業体制) の L2 (Sonnet) / L3 (Haiku) 委譲プロンプト全般
**出典**: 公式 "Prompting Claude Sonnet 5" + "What's new in Claude Sonnet 5" (platform.claude.com / 2026-07-07 取得) / community 実運用報告 (HN launch thread / CodeRabbit 実測 / claudefa.st 他 / 2026-06-30〜07-03)。調査記録は本ファイル制定セッション (2026-07-07) の 2 系統並列調査による。

## §1 挙動デルタ → `model-roster.md` §3（SSOT 退避済 / 2026-07-26 W2-M1-T2）

**Sonnet 5 のデルタ 1〜7 と「リテラル × over-delivery の両立解釈」は `.claude/rules/model-roster.md` §3 が正本**（モデル名の束縛は roster 1 枚に集約する / ADR-0011 決定 2）。Haiku 4.5 の挙動（未確認）も同節。

本ファイル以降の「**デルタ N**」表記は roster §3 の番号を指す（**移設で番号は変わっていない**）。本ファイルが持つのは**委譲プロンプトの書き方**のみであり、モデル世代交代時に更新するのは roster 側である。

## §2 Sonnet 5 委譲プロンプト必須 7 項

`hga-summoning.md` §tight brief 5-slot (objective / output format / tool guidance / task boundaries / primary_sources) を基底とし、以下を追加・強化する:

1. **スコープ全称明示**: 広く適用させたい範囲は列挙または全称で明示 (公式例: "Apply this formatting to every section, not just the first one")
2. **下方向フェンス**: 変更してよいファイルの白リスト + 「新規依存追加禁止 / 依頼外 helper 禁止 / 依頼外ファイル作成禁止 / git 操作禁止 / **scratchpad ディレクトリ（`AppData/Local/Temp/claude/...`）への成果物書込禁止**」を明記
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

- **`hga-summoning.md` の「Sonnet 5 は loose brief で under-deliver するため下調べ用途に不適」**: 公式のリテラル特性からの帰結として妥当。community 実測では「実装詳細の over-delivery」が優勢だが、これは `model-roster.md` §3 の両立解釈の通り矛盾しない。下調べ不適判定は**当面維持** (retrieval 主体タスクは Opus 優位という独立根拠あり) — W-R5 retro で再評価
- **「background meta-response 早期終了」(2026-07-04 Wave C 実測)**: community 裏付けゼロ (2026-07-07 調査時点)。Sonnet 5 モデル特性ではなく CC harness (v2.1.198 background 既定) 起因の可能性が高い。対策 (`disallowedTools: [Agent]` + boilerplate) は原因不問で有効なため**継続**
- **未確認事項** (使用時に要実測): Haiku 4.5 の effort param 可否 / Haiku 4.5 への adaptive thinking 適用有無 / トークナイザ 30% 増のコンテンツ種別ごとの実際値

## 権限等級

本ファイルの変更: **PM級**

## 参照

- `.claude/rules/model-roster.md` §3 (**挙動デルタの正本** / デルタ 1〜7 + 両立解釈 / 2026-07-26 移設)
- `.claude/rules/hga-summoning.md` (§tight brief 5-slot / §Sonnet L2 委譲時の追加防御 / §loose brief の唯一例外)
- `CLAUDE.md` §作業体制 (3.5 層委譲モデル) / §担当層の判断基準
- 公式: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5
- 公式: https://platform.claude.com/docs/en/about-claude/models/whats-new-sonnet-5
- 公式: https://code.claude.com/docs/en/sub-agents
- community: https://www.coderabbit.ai/blog/claude-sonnet-5-review (レビュー recall 実測) / HN launch thread (over-delivery / 制約 drop-through 報告)
