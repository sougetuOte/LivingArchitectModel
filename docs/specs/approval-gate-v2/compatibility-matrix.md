# Compatibility Matrix — CC バージョン × defaultMode × 配置

## メタ情報

| 項目 | 内容 |
|------|------|
| バージョン | v1.0.1 |
| 最終更新 | 2026-07-02 |
| 関連 ADR | [ADR-0008](../../adr/0008-approval-gate-redesign.md) — 承認ゲート再設計 |
| 検証 CC バージョン | 2.1.195 (2026-06-30 実機) |
| 起票 | Milestone B-5 Phase B-3 / doc-writer |
| 権限等級 | PM 級 |

---

## 概要

本文書は Claude Code (CC) の `permissions.defaultMode` について、CCバージョン・設定ファイル配置・LAM 推奨度を一覧化した SSOT である。
LAM ユーザーが「自分の CC バージョンでこの mode はどう動くか」「どこに設定を書けば有効か」を即判定できることを目的とする。
ADR-0008 軸 4 の判断根拠として参照され、`CLAUDE.md § Execution Permission Modes (Advisory)` と整合する。
実機検証は CC 2.1.195 (2026-06-30) を基準とし、各ピボットバージョンでの挙動差分を示す。
本文書の情報は CC のアップデートにより陳腐化するため、末尾の「更新トリガー」に従い都度更新すること。

---

## 1. メイン表 — CC バージョン × defaultMode

| mode | < v2.1.83 | v2.1.83–141 | v2.1.142–177 | v2.1.178+ | LAM 推奨度 |
|------|-----------|-------------|--------------|-----------|-----------|
| `default` | 有効 [^d1] | 有効 | 有効 | 有効 | (中立) |
| `acceptEdits` | 有効 | 有効 | 有効 | 有効 | (中立) |
| `plan` | 有効 | 有効 | 有効 | 有効 | (中立) |
| `auto` | 存在しない | 有効 [^a1] | 有効 + self-grant 防止 [^a2] | 有効 + subagent 境界 [^a3] | **SHOULD** |
| `dontAsk` | 有効 | 有効 | 有効 + self-grant 防止 [^a2] | 有効 + subagent 境界 [^a3] | NOT RECOMMENDED |
| `bypassPermissions` | 有効 [^b1] | 有効 | 有効 + self-grant 防止 [^a2] | 有効 + subagent 境界 [^a3] | NOT RECOMMENDED |

[^d1]: `default` は CC 初期から存在する基本動作。全操作で ask prompt が出る。Anthropic 実測で 93% 承認の「形骸化」状態になりやすい。
[^a1]: v2.1.83 で auto mode 初導入。Sonnet 4.6 classifier + soft_deny 55 件 + hard_deny 1 件の三層防御が有効になる。
[^a2]: v2.1.142 で self-grant 防止が追加。`auto` / `dontAsk` / `bypassPermissions` を project / local 配置で設定しても **無視** される。user / managed 配置のみ有効。
[^a3]: v2.1.178 で subagent 起動前 classifier が動作。subagent frontmatter の `permission_mode` は **ignored**。
[^b1]: `bypassPermissions` は全承認スキップ。LAM 規律の hook (C1–C5) のみが安全網として稼働する。`/quick-load` 強警告対象。

---

## 2. 配置別表 — mode × 設定ファイル配置

配置の優先度（高 → 低）: managed > CLI args > local > project > user

| mode | managed [^p1] | user [^p2] | project [^p3] | local [^p4] |
|------|--------------|-----------|--------------|------------|
| `default` | 有効 | 有効 | 有効 | 有効 |
| `acceptEdits` | 有効 | 有効 | 有効 | 有効 |
| `plan` | 有効 | 有効 | 有効 | 有効 |
| `auto` | 有効 | 有効 | **無視** (v2.1.142+) | **無視** (v2.1.142+) |
| `dontAsk` | 有効 | 有効 | **無視** (v2.1.142+) | **無視** (v2.1.142+) |
| `bypassPermissions` | 有効 | 有効 | **無視** (v2.1.142+) | **無視** (v2.1.142+) |

[^p1]: managed: `/etc/claude-code/managed-settings.json` (POSIX) / `%PROGRAMDATA%\ClaudeCode\managed-settings.json` (Windows)。組織管理者が上書き禁止で配置するレイヤー。
[^p2]: user: `~/.claude/settings.json`。LAM が `auto` mode を推奨する際の **設定先**。
[^p3]: project: `<project>/.claude/settings.json`。リポジトリにコミットされるが、`auto` / `dontAsk` / `bypassPermissions` は v2.1.142+ で self-grant 防止により無視される。
[^p4]: local: `<project>/.claude/settings.local.json`。`.gitignore` 推奨のローカル専用設定。`auto` 系は v2.1.142+ で無視される点は project と同様。

### 設定例 (LAM 推奨 — user 配置)

```json
// ~/.claude/settings.json
{
  "permissions": {
    "defaultMode": "auto"
  }
}
```

> v2.1.142 以降、`auto` を `<project>/.claude/settings.json` に書いても無視される。
> LAM ユーザーは必ず `~/.claude/settings.json`（user 配置）に記述すること。

---

## 3. 実機検証 — `claude auto-mode defaults`

### 手順

```bash
# CC 2.1.83+ で利用可
claude auto-mode defaults
```

### 検証結果 (CC 2.1.195 / 2026-06-30)

| カテゴリ | 件数 | 概要 |
|---------|------|------|
| `allow` | 16 件 | auto 承認される例外条件 |
| `soft_deny` | 55 件 | classifier が ask prompt に昇格させる操作 |
| `hard_deny` | 1 件 | Data Exfiltration (長文 prose) のみ |
| `environment` | 存在 | 環境変数関連の設定 |

> 各項目の prose 全文はサイズ過大のため本文書に転載しない。
> 実機で `claude auto-mode defaults` を実行して取得すること。

### 注記 (未確認事項)

`rm -rf /` 系の circuit breaker は実機の `hard_deny` リストには含まれていなかった（1 件は Data Exfiltration のみ）。
circuit breaker が `hard_deny` とは別ロジックで実装されている可能性がある。
公式ドキュメントで追跡中（「未確認事項」セクション参照）。

---

## 4. Pivotal Versions

| バージョン | 追加・変更 | ステータス |
|----------|-----------|-----------|
| v2.1.83 | `auto` mode 初導入 / Sonnet 4.6 classifier + soft_deny + hard_deny 三層防御 | 確認済 |
| v2.1.126 | `bypassPermissions` が Protected paths も auto-approve | 確認済 |
| v2.1.142 | self-grant 防止: `auto` / `bypassPermissions` / `dontAsk` を project / local 配置で書いても無視 | 確認済 |
| v2.1.158 | Bedrock / Vertex 環境で `CLAUDE_CODE_ENABLE_AUTO_MODE=1` が必要 | 確認済 |
| v2.1.172 | 役割不明 / ADR-0008 言及あり | 未確認 |
| v2.1.178 | subagent 起動前 classifier 動作 / subagent frontmatter `permission_mode` は ignored | 確認済 |
| v2.1.182 | git destructive 操作を soft_deny に追加 [^g1] | 確認済 |
| v2.1.195 | 本セッション実機検証バージョン | 検証済 (2026-06-30) |

[^g1]: v2.1.182 で soft_deny に追加された git destructive 操作: `git reset --hard` / `git checkout -- .` / `git restore .` / `git clean -fd` / `git stash drop` / `git stash clear`

**出典**: context7 + [code.claude.com](https://code.claude.com) (2026-06-30 調査)

---

## 5. LAM 規律との関係 (ADR-0008 軸 4)

AutoMode (soft_deny 三層防御) の採用後も、以下の LAM 規律制御は **mode に依存せず** 稼働する。

| 制御 | 概要 | 永続性 |
|------|------|--------|
| C1: PM 級ファイル ask | `docs/specs/` 等の初回編集は ask / 2 回目以降はセッションスコープ降格 | 永続 |
| C2: incident-patterns.yaml 動的 deny | incident-patterns.yaml の動的 deny リスト照合 | 永続 |
| C3: AUTONOMOUS 統治ファイル不可侵 | AUTONOMOUS フェーズの統治ファイル書込は不可逆 deny | 永続 |
| C4: 不可逆 + 外部送信 hook 重ね掛け | AutoMode と二重防御 (暫定) | 暫定 [^c4] |
| C5: subagent 起動時の権限境界 | AUTONOMOUS + autonomous skill 配下のみ ask | 永続 (Phase B-2 実装済 / commit 4a97fe2) |

[^c4]: C4 は AutoMode 採用安定後に Phase C 末で撤去を判定する。撤去 3 条件: (1) 採用率の一定期間観察、(2) 過去 90 日インシデントなし、(3) soft_deny 完全性確認。

> `bypassPermissions` 使用時: AutoMode 三層防御が無効となるため、C1–C5 の hook のみが安全網として稼働する。
> この設定は LAM で NOT RECOMMENDED とする。

---

## 6. 更新トリガー

本文書は以下のイベント発生時に更新すること（PM 級 / 人間承認必須）:

- CC の新バージョンリリースで `permissions.defaultMode` の挙動が変わった場合
- `auto-mode defaults` の出力件数 (allow / soft_deny / hard_deny) が変化した場合
- self-grant 防止の対象 mode が追加・削除された場合
- Bedrock / Vertex 等の環境依存条件が変化した場合
- 未確認事項のいずれかが確認できた場合

---

## 7. 未確認事項

| # | 内容 | 追跡先 |
|---|------|--------|
| U-1 | v2.1.172 の具体的な変更内容 | context7 / code.claude.com |
| U-2 | circuit breaker (`rm -rf /` 系) が `hard_deny` と別ロジックかどうか | `claude auto-mode defaults` 詳細 / 公式 docs |
| U-3 | GH #27139 / #9924 / #13077 (ワイルドカード未尊重バグ) の解決状況 | GitHub Issues |
| U-4 | managed > CLI args > local > project > user の厳密な多段 hook precedence | 公式 permissions docs |

---

## 参照

- [ADR-0008](../../adr/0008-approval-gate-redesign.md) — 承認ゲート再設計（自己責任モデル / Accepted）
- [CLAUDE.md § Execution Permission Modes (Advisory)](../../../CLAUDE.md) — LAM SHOULD 根拠
- [docs/internal/07_SECURITY_AND_AUTOMATION.md](../../internal/07_SECURITY_AND_AUTOMATION.md) — AutoMode Advisory 詳細
- [.claude/rules/permission-levels.md](../../../.claude/rules/permission-levels.md) — PG/SE/PM 権限等級
- [.claude/rules/security-commands.md](../../../.claude/rules/security-commands.md) — コマンド許可マトリクス (D1/D4)
- GitHub Issues: [#27139](https://github.com/anthropics/claude-code/issues/27139) / [#9924](https://github.com/anthropics/claude-code/issues/9924) / [#13077](https://github.com/anthropics/claude-code/issues/13077) — ワイルドカード未尊重バグ
