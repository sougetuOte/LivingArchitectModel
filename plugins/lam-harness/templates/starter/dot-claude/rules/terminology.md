# 用語ガイドライン

> **starter テンプレート**: 初回だけ敷かれます。以後はあなたの資産です。
> 階層の**構造**は汎用ですが、Milestone の命名規則などはプロジェクト固有のため、
> 更新が届かない starter 層に置いています。

## §1 用語階層

作業単位は以下の 4 層で構成する。

```
Project
  └─ Milestone（例: B-4, B-5）
       └─ Step（例: PLANNING, BUILDING, AUDITING）
            └─ Wave（例: Wave 1, Wave 1.5）
                 └─ Task（例: PR-A, T9）
```

| 用語 | 位置 | 形式の例 |
|------|------|---------|
| Project | 最上位 | <記入> |
| Milestone | Project 直下 | B-4, B-5 |
| Step | Milestone 直下 | PLANNING, BUILDING, AUDITING |
| Wave | Step 直下 | Wave 1, Wave 1.5 |
| Task | Wave 直下 | PR-A, T9 |

### 補助用語

| 用語 | 説明 |
|------|------|
| **Phase** | PLANNING / BUILDING / AUDITING の三フェーズ規律（`phase-rules.md` が定義）。「どのモードで作業するか」。Step とは独立しており、名前が一致しても混同しない |

## §2 区別が要る 3 組

| 組 | 区別 |
|:--|:--|
| Milestone / Step | Milestone は「何を達成するか」の束。Step は「どの段階にいるか」 |
| Step / Phase | Phase は**規律**の文脈、Step は**進行位置**の文脈で使う |
| Wave / Task | Wave は複数 Task をまとめた実装のバッチ。Task は個別の作業単位 |

## §3 正例・誤例

| | 表現 |
|---|------|
| 誤 | 「B-4 の Wave 1 PLANNING を開始する」（PLANNING は Step であり Wave の修飾語ではない） |
| 正 | 「B-4 PLANNING Step の Wave 1 を開始する」 |
| 誤 | 「B-4 Wave 1a（後処理）」 |
| 正 | 「B-4 Wave 1.5（後処理・影響波及修正）」 |
| 誤 | 「Wave PR-A を実施する」（PR-A は Task） |
| 正 | 「Wave 1 の Task PR-A を実施する」 |

## §4 命名規則（**要記入 / 下記は出発点**）

### コミットメッセージ

Conventional Commits に従い、スコープに Milestone を書く。

```
<type>(<milestone>): <subject>
```

| type | 用途 |
|------|------|
| `feat` | 新機能・新仕様の実装 |
| `fix` | バグ修正・誤用修正 |
| `docs` | ドキュメント・仕様書更新 |
| `chore` | 管理作業 |
| `refactor` | 振る舞いを変えないリファクタリング |
| `test` | テスト追加・修正 |

### 文書参照

- 文書内の相互参照は **§ 見出し表記**を使う（行番号は挿入でずれる）
- 節番号の挿入は末尾追加を既定とし、途中挿入が必要なら枝番（`§4.5`）を使う

## §5 権限等級

本ファイルの変更: **PM 級**（`.claude/rules/` 配下）。
