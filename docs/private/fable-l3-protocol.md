# Fable-Alembic L3 Protocol (LAM 適用)

**制定日**: 2026-07-07
**根拠**: HGA #11 (案 D 直交軸接続確定) + HGA #12 (案 D 具体化 / 修正 3 点反映) / `docs/artifacts/hga-summon-log.md` §11-12
**位置づけ**: LAM は Fable-Alembic を L3 (深く同化) で運用する。本ファイルは **L3 導入の宣言と原典の所在**を持つ。
**等級**: SE 級 (`docs/` 配下)
**射程 (2026-09-04 分割後)**: **作者環境限定**。§0-§2 のみを持ち、参照者は `.claude/hooks/pre-tool-use.py` と `.claude/tests/hooks/test_outbound_write_ban.py` の 2 点。
**本ハーネスの動作に本ファイルは不要である** —— 実行規律の正本は `docs/internal/08_EXECUTION_DISCIPLINE.md`。

## §0 導入宣言 (`etc-to-alembic` テンプレ準拠 / L3)

> 以下は `D:\work7\etc-to-alembic\README.md` §他プロジェクト向けセットアップテンプレートの原文を L3 で貼付したもの。SSOT の貼付場所は本ファイル (`docs/private/fable-l3-protocol.md` §0)。

### Fable-Alembic 連携 (受け入れレベル: **L3**)

Fable 5 の judgment heuristics を継承する `D:\work7\Fable-Alembic\` を、レベル **L3** で参照する。

#### 参照ファイル
- SSOT: `D:\work7\Fable-Alembic\knowledge\`
- 連携規律: `D:\work7\etc-to-alembic\README.md`

#### 読み込み規律
(レベル別マトリクス `D:\work7\etc-to-alembic\README.md` §レベル別の読み込み規律マトリクス に従う / L3 = 全 MUST 発動)

#### 書き込み境界 (全レベル共通、MUST NOT)
- `D:\work7\Fable-Alembic\` 配下への書き込み・編集は行わない
- Alembic への提案・観察の受け渡しは `D:\work7\etc-to-alembic\handoff\` を経由する

#### 模倣禁止 (L4 禁止)
- Fable の文体・比喩をコピーしない。判断の理由 (第 0 原則の 3 変数) を継ぐ
- 「Fable ならこう言いそう」を出力する誘惑にブレーキをかける

---

## §1 L3 宣言

LAM は Fable-Alembic (`D:\work7\Fable-Alembic\`) を **L3** で運用する
(`D:\work7\etc-to-alembic\README.md` §受け入れレベル 準拠)。

参考実装: `C:\etm-diary` (L3 運用中 / `fable-heritage.md`)。

L3 の意味: 第0原則を default 判断基準として採用 / 自己監査 14 項目を完了宣言前ゲート / 体験シミュを完了宣言 3 点で MUST 発動 / 実行プロトコル F0-F4 を BUILDING の運転規則として採用。

## §2 参照 SSOT (Outbound Write Ban 全レベル共通)

| # | ファイル | 用途 |
|---|---------|------|
| 1 | `D:\work7\Fable-Alembic\knowledge\Fable行動規範.md` | 判断規範 (第0原則 + 系(1)(2)(3)) |
| 2 | `D:\work7\Fable-Alembic\knowledge\自己監査チェックリスト.md` | 完了宣言前 14 項目 |
| 3 | `D:\work7\Fable-Alembic\knowledge\体験シミュレーション・プロトコル.md` | 60 秒実況 + §6 位置決め |
| 4 | `D:\work7\Fable-Alembic\knowledge\実行プロトコル.md` | F0-F4 運転規則 |
| 補 | `D:\work7\Fable-Alembic\knowledge\判断差分の予測.md` | 導入 retro 1 回のみベースライン照合 (§8 参照) |

**Outbound Write Ban** (全レベル共通 / MUST NOT): `D:\work7\Fable-Alembic\` 配下への書き込み・編集は行わない。
Alembic への感想・提案の受け渡しは `D:\work7\etc-to-alembic\handoff\` を経由する。

パス移動時の対応: Fable-Alembic 側のリポジトリ位置が変更された場合、本節のパスのみ更新すれば LAM 側の他規律は無変更で吸収する。**ただし機構側（下記）は本節を自動追随しないため、両方を更新する**（drift 検査あり）。

**機構（2026-07-27 制定 / 2026-09-04 に project 層へ移設）**: 本節は **`.claude/hooks-local/outbound-write-ban.py`** の `_BAN_ROOTS` が、**独立した PreToolUse hook** として `exit 2`（blocking）で執行する。allow 対は `_ALLOW_ROOTS`（handoff 経路 / ADR-0008 D1）。テストと境界条件は `.claude/tests/hooks/test_outbound_write_ban.py`（セパレータ 4 形 / `etc-to-alembic` の誤 deny 回帰 / 条文との drift 検査 / hook 終了コードの end-to-end）。

**移設の理由**: 配布形態を plugin へ移すにあたり `.claude/hooks/pre-tool-use.py` は**配布物**になった。作者マシンの絶対パスをそこに残すと、利用者は「動いているように見えて何も守らないコード」を受け取る（**31 回のリリースで実際に配られ続けていた**）。D-1 design §5 決定 D4 が定めた目標状態「**hook・テスト・条文がすべて配布物から外れる**」を本移設で達成した。

**分離しても実効性は落ちない**: hook は設定レベル間で **merge され置換されず**、`exit 2` は他 hook の `permissionDecision: allow` では覆せない（公式 / fail-secure）。これは不変条件「私的規範は『追加』のみ許し『置換』を許さない」に厳密に一致する。

**条文を残すのは、機構が沈黙したときにそれを知るため**（誕生ゲート設計 §1.3 = 不可逆ガードの R1 + R3 複宛先）。**Bash 経由の書込は本機構の対象外**（`file_path` を持たないため判定に到達しない / 対処は Layer 1 = `permissions.deny` の領分）。

## §3-§9 → `docs/internal/08_EXECUTION_DISCIPLINE.md` へ分離（2026-09-04）

本ファイルが持っていた **§3 帳簿単一原則 / §4 自己監査 14 項目 / §5 体験シミュ発火点 / §6 F0-F4 埋込 /
§7 L4 禁止 / §8 判断差分予測の扱い / §9 観測チャンネル対応表** は **LAM の製品価値の中核**であり、
`docs/internal/08_EXECUTION_DISCIPLINE.md` へ移した（**節番号は維持** / 参照側の変更はファイル名のみ）。

**分離の根拠**: `docs/specs/d-1-distribution-boundary/design.md` §4 は本ファイルを「**S（要分割）を認める理由**」の
実例として名指しし、こう書いていた —— 「2 値判定を強制すると『**製品の中核を私物として捨てる**』か
『私物を配り続ける』の二択になり、**どちらも誤りである**」。にもかかわらず D-1 の判定は **X（丸ごと私物）**で、
**243 行中 25 行（10%）**の私的記述のために約 218 行の製品中核が配布境界の外へ出ていた。

**実害**: 2026-08-29 に修正した「`CLAUDE.md` の実況発火点から `PLANNING` 修飾が脱落していた」件は、
**正本が非ロード側にあったため**の drift である。

経緯: `docs/artifacts/2026-09-04-magi-distribution-form.md` §13（MAGI + gabriel 2 巡 + HGA #29）。

## §10 権限等級

本ファイルの変更: **SE 級**（`docs/` 配下 / `.claude/rules/permission-levels.md` §ファイルパスベースの分類）。

> **2026-09-04 是正**: 旧記述は「**PM級**（`.claude/rules/` 配下）」だったが、本ファイルは誕生ゲート取引 #13
> （2026-08-13）で `.claude/rules/` から外れており、**記述が約 3 週間追随していなかった**。
>
> ただし §2 は `_OUTBOUND_WRITE_BAN_ROOTS` の SSOT であり、変更すると
> `.claude/tests/hooks/test_outbound_write_ban.py` の drift 検査が落ちる（機構側で保護されている）。

## §11 参照

- **実行規律の正本**: `docs/internal/08_EXECUTION_DISCIPLINE.md`（§3-§9 / 2026-09-04 分離）
- HGA 召喚記録: `docs/artifacts/hga-summon-log.md` §11-12（案 D 確定と具体化）/ #29（本分割）
- Fable-Alembic knowledge: `D:\work7\Fable-Alembic\knowledge\`（§2 参照 SSOT）
- 連携規律: `D:\work7\etc-to-alembic\README.md`
- 機構: `.claude/hooks/pre-tool-use.py`（`_OUTBOUND_WRITE_BAN_ROOTS` / `_OUTBOUND_WRITE_ALLOW_ROOTS`）
  / `.claude/tests/hooks/test_outbound_write_ban.py`（条文との drift 検査）
