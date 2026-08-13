# D-1 S 分割の抜き出し集約（2026-08-13 / W2-D1-T4）

**このファイルは開発者個人の私的記録である。配布先では削除して構わない。**

D-1 のユーザー判定（`docs/artifacts/d-1-evidence-2026-07-28.md` §6）で **S（要分割）** と
された 5 ファイルから抜いた私的部分を、ここに 1 ファイルで集約する（tasks.md T4 の完了条件）。

## 軸の記録（各件 1 行 / 「誰のものか」であって「要るか」ではない）

| ファイル | 抜いたもの | 軸の確認 |
|:--|:--|:--|
| `CLAUDE.md` | パス表記例の実パス `D:/work7/...` → 汎用例 `D:/path/to/repo/...` に置換 | 開発者の作業ディレクトリ名。記述自体（パス表記規則）は P として残した |
| `core-identity.md` | 第0原則の由来表記（Fable-Alembic L3）と原典 2 冊への絶対パス | 外部私有リポジトリへの参照。第0原則の 3 変数本体は P として残した |
| `hga-summoning.md` | 再送コストの実測数値 `$0.15` / `$1-4` → 桁の比較表現 + 実測記録への参照に置換 | 開発者個人の課金実績。行 122 は P 資産（`model-roster.md` §4）への参照のため据え置き |
| `permission-levels.md` | 「迷った場合」の原典絶対パスと L3 準拠表記 | 外部私有リポジトリへの参照。3 変数による判定手順は P として残した |
| `phase-rules.md` | 見出し 4 箇所の「Fable-Alembic L3」帰属表記 | 外部規範への帰属ラベル。体験シミュ・F0-F4 の規律本体は P として残した |

## 抜き出した原文（逐語）

### CLAUDE.md（行 80-81 / 置換前）

```
- **パスはフォワードスラッシュ**で書く（`D:/work7/...` または相対 `.claude/hooks/`）。
  バックスラッシュ（`D:\work7\...`）は bash がエスケープ文字として食い、パスが潰れて失敗する
```

### core-identity.md（§第0原則 / 置換・削除前）

```
## 第0原則 (Fable-Alembic L3 由来 / 権限等級の基底原理)

LAM は Fable-Alembic を L3 で運用する (`.claude/rules/fable-l3-protocol.md` §1)。
```

```
次の 3 変数で決める (原典: `D:\work7\Fable-Alembic\knowledge\Fable行動規範.md`):
```

```
この 3 変数と `D:\work7\Fable-Alembic\knowledge\体験シミュレーション・プロトコル.md` から判断を再導出する。
規則の字面が第 0 原則と食い違うなら、第 0 原則が勝つ (原典冒頭)。
```

### hga-summoning.md（§ステートレス規律 / 置換前）

```
再送コストは 1 回あたり概算 $0.15 程度（フル召喚 $1-4 とは別物）であり、
```

### permission-levels.md（§迷った場合 / 置換前）

```
まず**第 0 原則の 3 変数**で判定する (`.claude/rules/core-identity.md` §第 0 原則 / `.claude/rules/fable-l3-protocol.md` §1 準拠 / 原典: `D:\work7\Fable-Alembic\knowledge\Fable行動規範.md`):
```

### phase-rules.md（見出し 4 箇所 / 置換前）

```
### 承認要求提出直前の体験シミュ (MUST / Fable-Alembic L3)
### F0-F4 埋込 (Fable-Alembic L3 / 実行プロトコル準拠)
### F4 (全体検証 / Fable-Alembic L3 / 実行プロトコル準拠)
### 監査レポート提出直前の体験シミュ (MUST / Fable-Alembic L3)
```

## 付随した機械的パス追随（判定を伴わない / T3 の帰結）

`fable-l3-protocol.md` が `docs/private/` へ移動したため、残存 R1 ファイル内の参照パスを
`docs/private/fable-l3-protocol.md` へ更新した: `CLAUDE.md`（3 箇所）/ `phase-rules.md`（7 箇所）/
`auto-generated/rule-001.md`（1 箇所）。所有者環境では従来どおり辿れる。

## 参照

- 判定: `docs/artifacts/d-1-evidence-2026-07-28.md` §6（ユーザー本人 / 2026-08-13）
- 設計: `docs/specs/d-1-distribution-boundary/design.md` §3-§4（D2 / D3）
- 台帳: `docs/artifacts/clause-gate-ledger.md` §B 取引 #13
